import type { Metadata } from "next";

import { Nav } from "@/components/nav";
import { ReactQueryProvider } from "@/lib/react-query/provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Liqflow hands-on test",
  description: "Binance TH order book → API → Postgres → API → BFF → frontend.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ReactQueryProvider>
          <main className="mx-auto max-w-4xl">
            <Nav />
            {children}
          </main>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
