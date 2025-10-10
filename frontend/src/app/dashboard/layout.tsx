"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Bot, 
  MessageSquare, 
  Brain, 
  Target, 
  Trophy, 
  Settings, 
  Menu, 
  X,
  LogOut,
  User
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Bot },
  { name: "Chat", href: "/dashboard/chat", icon: MessageSquare },
  { name: "AI", href: "/dashboard/ai", icon: Brain },
  { name: "Study", href: "/dashboard/study", icon: Target },
  { name: "Quiz", href: "/dashboard/quiz", icon: Trophy },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-cyber-black flex">
      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-cyber-black/80 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen ? 0 : -300 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed inset-y-0 left-0 z-50 w-64 bg-cyber-dark border-r border-cyber-blue/20 lg:translate-x-0 lg:static lg:inset-0"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-cyber-blue/20">
            <div className="flex items-center space-x-3">
              <Bot className="w-8 h-8 text-cyber-blue" />
              <span className="text-xl font-orbitron font-bold text-cyber-blue">
                ZEPHY JR.
              </span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-cyber-light hover:text-cyber-blue transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-300 group ${
                    isActive
                      ? "bg-gradient-to-r from-cyber-blue/20 to-cyber-magenta/20 text-cyber-blue border border-cyber-blue/30"
                      : "text-cyber-light/70 hover:text-cyber-blue hover:bg-cyber-blue/10"
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-cyber-blue/20">
            <div className="flex items-center space-x-3 p-3 rounded-lg bg-cyber-gray/50">
              <div className="w-8 h-8 bg-gradient-to-r from-cyber-blue to-cyber-magenta rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-cyber-black" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-cyber-light truncate">
                  Admin User
                </p>
                <p className="text-xs text-cyber-light/60 truncate">
                  admin@zephyjr.com
                </p>
              </div>
              <button className="text-cyber-light/60 hover:text-cyber-blue transition-colors">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top bar */}
        <header className="bg-cyber-dark border-b border-cyber-blue/20 px-4 py-4 lg:px-6">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-cyber-light hover:text-cyber-blue transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <div className="flex items-center space-x-4">
              <div className="hidden sm:block">
                <h1 className="text-lg font-orbitron font-bold text-cyber-blue">
                  Control Panel
                </h1>
              </div>
              
              {/* Status indicator */}
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-cyber-green rounded-full cyber-pulse"></div>
                <span className="text-sm text-cyber-light/60">Online</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}