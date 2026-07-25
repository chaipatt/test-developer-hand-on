// Command migration-report prints a before/after schema-version report around
// the golang-migrate migrations in db/, using the official Postgres driver
// (github.com/golang-migrate/migrate/v4/database/postgres).
//
// It reports the current version, rolls back one step, then re-applies it, so
// the newest migration (currently 000004_market_stats) is exercised in both
// directions and the version transition is printed at each hop.
//
// Usage:
//
//	DSN='postgres://liqflow:liqflow@localhost:5433/liqflow?sslmode=disable&search_path=public' \
//	  go run . -path ../../db
package main

import (
	"errors"
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/golang-migrate/migrate/v4"
	"github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"

	"database/sql"

	_ "github.com/jackc/pgx/v5/stdlib" // registers the "pgx" database/sql driver
)

func version(m *migrate.Migrate) string {
	v, dirty, err := m.Version()
	if errors.Is(err, migrate.ErrNilVersion) {
		return "none (no migrations applied)"
	}
	if err != nil {
		log.Fatalf("read version: %v", err)
	}
	return fmt.Sprintf("%d (dirty=%v)", v, dirty)
}

func step(m *migrate.Migrate, n int) {
	if err := m.Steps(n); err != nil && !errors.Is(err, migrate.ErrNoChange) {
		log.Fatalf("steps(%d): %v", n, err)
	}
}

func main() {
	path := flag.String("path", "../../db", "path to migrations directory")
	flag.Parse()

	dsn := os.Getenv("DSN")
	if dsn == "" {
		log.Fatal("set DSN env var, e.g. postgres://liqflow:liqflow@localhost:5433/liqflow?sslmode=disable&search_path=public")
	}

	db, err := sql.Open("pgx", dsn)
	if err != nil {
		log.Fatalf("open db: %v", err)
	}
	defer db.Close()

	driver, err := postgres.WithInstance(db, &postgres.Config{})
	if err != nil {
		log.Fatalf("postgres driver: %v", err)
	}

	m, err := migrate.NewWithDatabaseInstance("file://"+*path, "postgres", driver)
	if err != nil {
		log.Fatalf("migrate init: %v", err)
	}

	fmt.Println("=== golang-migrate before/after report ===")
	fmt.Printf("driver:  github.com/golang-migrate/migrate/v4/database/postgres\n")
	fmt.Printf("source:  file://%s\n\n", *path)

	fmt.Printf("BEFORE (current):  version %s\n", version(m))

	step(m, -1) // roll back the newest migration (000004 down)
	fmt.Printf("after down 1:      version %s\n", version(m))

	step(m, 1) // re-apply it (000004 up)
	fmt.Printf("AFTER up 1:        version %s\n", version(m))

	fmt.Println("\nOK: newest migration verified in both directions (down then up).")
}
