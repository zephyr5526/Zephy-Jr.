"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Bot, Zap, Brain, Target, Trophy, Settings, LogIn } from "lucide-react";
import Link from "next/link";

export default function Home() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const features = [
    {
      icon: Bot,
      title: "Bot Control",
      description: "Start, stop, and monitor your Zephy Jr. bot instances",
      color: "from-cyber-blue to-cyber-magenta",
    },
    {
      icon: Brain,
      title: "AI Integration",
      description: "Configure AI models and personality settings",
      color: "from-cyber-green to-cyber-blue",
    },
    {
      icon: Target,
      title: "Study Tracking",
      description: "Monitor focus sessions and study goals",
      color: "from-cyber-yellow to-cyber-green",
    },
    {
      icon: Trophy,
      title: "Points System",
      description: "Track user engagement and leaderboards",
      color: "from-cyber-purple to-cyber-magenta",
    },
    {
      icon: Zap,
      title: "Real-time Chat",
      description: "Live chat monitoring and message management",
      color: "from-cyber-blue to-cyber-green",
    },
    {
      icon: Settings,
      title: "System Config",
      description: "Configure bot settings and API keys",
      color: "from-cyber-magenta to-cyber-purple",
    },
  ];

  return (
    <div className="min-h-screen bg-cyber-black relative overflow-hidden">
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

      <div className="relative z-10 container mx-auto px-4 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center mb-16"
        >
          <motion.div
            className="inline-block mb-6"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Bot className="w-20 h-20 text-cyber-blue mx-auto mb-4 cyber-glow" />
          </motion.div>
          
          <h1 className="text-6xl md:text-8xl font-orbitron font-black mb-6 cyber-text-glow">
            <span className="bg-gradient-to-r from-cyber-blue via-cyber-magenta to-cyber-green bg-clip-text text-transparent">
              ZEPHY JR.
            </span>
          </h1>
          
          <p className="text-2xl md:text-3xl text-cyber-light/80 mb-4 font-light">
            Your Stream&apos;s Smartest, Sassiest Sidekick
          </p>
          
          <motion.div
            className="text-4xl mb-8"
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            🤖
          </motion.div>
          
          <p className="text-lg text-cyber-light/60 max-w-2xl mx-auto mb-12">
            A full-stack Nightbot-style control system with AI personality, 
            study tools, multi-API integration, and cloud-ready architecture.
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={isLoaded ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.1 * index, ease: "easeOut" }}
              whileHover={{ 
                scale: 1.05,
                rotateY: 5,
                transition: { duration: 0.3 }
              }}
              className="cyber-card cyber-hover group cursor-pointer"
            >
              <div className={`w-16 h-16 bg-gradient-to-r ${feature.color} rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-8 h-8 text-cyber-black" />
              </div>
              
              <h3 className="text-2xl font-orbitron font-bold text-cyber-blue mb-4 group-hover:text-cyber-magenta transition-colors duration-300">
                {feature.title}
              </h3>
              
              <p className="text-cyber-light/70 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
          className="text-center"
        >
          <div className="cyber-card max-w-2xl mx-auto">
            <h2 className="text-3xl font-orbitron font-bold text-cyber-blue mb-6">
              Ready to Take Control?
            </h2>
            
            <p className="text-cyber-light/80 mb-8">
              Access the full control panel to manage your bot, monitor chat activity, 
              and configure all settings in real-time.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/dashboard">
                <motion.button
                  className="cyber-button text-lg px-8 py-4"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Bot className="w-5 h-5 mr-2 inline" />
                  Enter Dashboard
                </motion.button>
              </Link>
              
              <motion.button
                className="cyber-button-secondary text-lg px-8 py-4"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <LogIn className="w-5 h-5 mr-2 inline" />
                Login
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={isLoaded ? { opacity: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="text-center mt-20 pt-8 border-t border-cyber-blue/20"
        >
          <p className="text-cyber-light/50">
            © 2024 Zephy Jr. Control Panel. Built with ❤️ and lots of caffeine.
          </p>
        </motion.footer>
      </div>
    </div>
  );
}