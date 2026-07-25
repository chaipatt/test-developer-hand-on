import { z } from "zod";

export const principalSchema = z.object({
  email: z.string(),
  role: z.enum(["user", "admin"]),
  description: z.string(),
  permissions: z.array(z.string()),
});

export type Principal = z.infer<typeof principalSchema>;
