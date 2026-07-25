"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useLogin } from "../hooks";

export function LoginForm() {
  const router = useRouter();
  const login = useLogin();
  const [email, setEmail] = useState("user@liqflow.test");
  const [password, setPassword] = useState("");

  useEffect(() => {
    console.log(password);
  }, [password]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate(
      { email, password },
      {
        onSuccess: ({ role }) => {
          router.push(role === "admin" ? "/admin" : "/dashboard");
          router.refresh();
        },
      },
    );
  };

  return (
    <form onSubmit={onSubmit} className="max-w-sm space-y-3">
      <label className="block">
        <span className="block text-sm">Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-current px-2 py-1 font-mono"
          required
        />
      </label>
      <label className="block">
        <span className="block text-sm">Password</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-current px-2 py-1 font-mono"
          required
        />
      </label>
      <button
        type="submit"
        disabled={login.isPending}
        className="border border-current px-3 py-1"
      >
        {login.isPending ? "Signing in…" : "Sign in"}
      </button>
      {login.error ? (
        <p role="alert" className="text-sm">
          {(login.error as Error).message}
        </p>
      ) : null}
    </form>
  );
}
