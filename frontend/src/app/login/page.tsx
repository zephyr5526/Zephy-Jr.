"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Bot, Eye, EyeOff, LogIn } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/components/providers/AuthProvider";
import { useToast } from "@/components/providers/ToastProvider";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { addToast } = useToast();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const success = await login(email, password);
      if (success) {
        addToast({
          type: "success",
          title: "Login Successful",
          message: "Welcome to Zephy Jr. Control Panel!",
        });
        router.push("/dashboard");
      } else {
        addToast({
          type: "error",
          title: "Login Failed",
          message: "Invalid email or password",
        });
      }
    } catch {
      addToast({
        type: "error",
        title: "Login Error",
        message: "An unexpected error occurred",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cyber-black flex items-center justify-center relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-cyber-grid opacity-20"></div>
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-cyber-blue/5 via-transparent to-cyber-magenta/5"></div>
      
      {/* Animated Background Elements */}
      <motion.div
        className="absolute top-20 left-20 w-32 h-32 bg-cyber-blue/10 rounded-full blur-xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        className="absolute bottom-20 right-20 w-40 h-40 bg-cyber-magenta/10 rounded-full blur-xl"
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.6, 0.3, 0.6],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <div className="relative z-10 w-full max-w-md px-4">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="cyber-card"
        >
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              className="inline-block mb-4"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Bot className="w-16 h-16 text-cyber-blue mx-auto cyber-glow" />
            </motion.div>
            
            <h1 className="text-3xl font-orbitron font-bold text-cyber-blue mb-2">
              ZEPHY JR.
            </h1>
            
            <p className="text-cyber-light/60">
              Control Panel Access
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-cyber-light mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="cyber-input"
                placeholder="admin@zephyjr.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-cyber-light mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="cyber-input pr-12"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-cyber-light/60 hover:text-cyber-blue transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              className="cyber-button w-full flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: loading ? 1 : 1.05 }}
              whileTap={{ scale: loading ? 1 : 0.95 }}
            >
              {loading ? (
                <div className="cyber-loading w-5 h-5 border-2 border-cyber-black border-t-transparent rounded-full"></div>
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  <span>Sign In</span>
                </>
              )}
            </motion.button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-cyber-light/50 text-sm">
              Your Stream&apos;s Smartest, Sassiest Sidekick 🤖
            </p>
          </div>
        </motion.div>

        {/* Back to Home */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-center mt-6"
        >
          <Link
            href="/"
            className="text-cyber-blue hover:text-cyber-magenta transition-colors text-sm"
          >
            ← Back to Home
          </Link>
        </motion.div>
      </div>
    </div>
  );
}