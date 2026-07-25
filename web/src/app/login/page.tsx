import { LoginForm } from "@/features/auth/components/login-form";

export default function LoginPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Sign in</h1>
      <p className="text-sm">
      3 users should have different passwords, and passwords should be kept secret from now on.
      </p>
      <LoginForm />
    </div>
  );
}
