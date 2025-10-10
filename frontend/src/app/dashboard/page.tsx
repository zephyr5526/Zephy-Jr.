"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Bot, 
  MessageSquare, 
  Users, 
  Activity, 
  Zap, 
  TrendingUp,
  Play,
  Pause,
  RotateCcw,
  AlertCircle
} from "lucide-react";

interface BotStatus {
  is_running: boolean;
  start_time?: string;
  last_activity?: string;
  message_count: number;
  error_count: number;
  video_id?: string;
}

interface Stats {
  total_messages: number;
  active_sessions: number;
  total_users: number;
  recent_activity: number;
}

export default function Dashboard() {
  const [botStatus, setBotStatus] = useState<BotStatus>({
    is_running: false,
    message_count: 0,
    error_count: 0,
  });
  const [stats, setStats] = useState<Stats>({
    total_messages: 0,
    active_sessions: 0,
    total_users: 0,
    recent_activity: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API calls
    const fetchData = async () => {
      try {
        // Simulate bot status fetch
        setBotStatus({
          is_running: true,
          start_time: new Date().toISOString(),
          last_activity: new Date().toISOString(),
          message_count: 1247,
          error_count: 3,
          video_id: "O-sJ8qOvNr4",
        });

        // Simulate stats fetch
        setStats({
          total_messages: 1247,
          active_sessions: 12,
          total_users: 89,
          recent_activity: 23,
        });
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleBotAction = async (action: "start" | "stop" | "restart") => {
    try {
      // Simulate API call
      console.log(`Bot ${action} action triggered`);
      
      if (action === "start") {
        setBotStatus(prev => ({ ...prev, is_running: true, start_time: new Date().toISOString() }));
      } else if (action === "stop") {
        setBotStatus(prev => ({ ...prev, is_running: false }));
      } else if (action === "restart") {
        setBotStatus(prev => ({ ...prev, is_running: false }));
        setTimeout(() => {
          setBotStatus(prev => ({ ...prev, is_running: true, start_time: new Date().toISOString() }));
        }, 1000);
      }
    } catch (error) {
      console.error(`Error ${action}ing bot:`, error);
    }
  };

  const getUptime = () => {
    if (!botStatus.start_time) return "0s";
    const start = new Date(botStatus.start_time);
    const now = new Date();
    const diff = now.getTime() - start.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    return `${hours}h ${minutes}m ${seconds}s`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="cyber-loading w-8 h-8 border-2 border-cyber-blue border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-orbitron font-bold text-cyber-blue">
            Dashboard
          </h1>
          <p className="text-cyber-light/60 mt-1">
            Monitor and control your Zephy Jr. bot instances
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            botStatus.is_running 
              ? "bg-cyber-green/20 text-cyber-green border border-cyber-green/30" 
              : "bg-red-500/20 text-red-400 border border-red-500/30"
          }`}>
            {botStatus.is_running ? "Running" : "Stopped"}
          </div>
        </div>
      </div>

      {/* Bot Control Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="cyber-card"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-orbitron font-bold text-cyber-blue">
            Bot Control
          </h2>
          <Bot className="w-6 h-6 text-cyber-blue" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="space-y-2">
            <p className="text-sm text-cyber-light/60">Status</p>
            <p className={`text-lg font-semibold ${
              botStatus.is_running ? "text-cyber-green" : "text-red-400"
            }`}>
              {botStatus.is_running ? "Online" : "Offline"}
            </p>
          </div>
          
          <div className="space-y-2">
            <p className="text-sm text-cyber-light/60">Uptime</p>
            <p className="text-lg font-semibold text-cyber-light">
              {botStatus.is_running ? getUptime() : "0s"}
            </p>
          </div>
          
          <div className="space-y-2">
            <p className="text-sm text-cyber-light/60">Messages</p>
            <p className="text-lg font-semibold text-cyber-light">
              {botStatus.message_count.toLocaleString()}
            </p>
          </div>
          
          <div className="space-y-2">
            <p className="text-sm text-cyber-light/60">Errors</p>
            <p className="text-lg font-semibold text-cyber-light">
              {botStatus.error_count}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <motion.button
            onClick={() => handleBotAction(botStatus.is_running ? "stop" : "start")}
            className={`cyber-button flex items-center space-x-2 ${
              botStatus.is_running ? "bg-red-500 hover:bg-red-600" : ""
            }`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {botStatus.is_running ? (
              <>
                <Pause className="w-4 h-4" />
                <span>Stop Bot</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start Bot</span>
              </>
            )}
          </motion.button>

          <motion.button
            onClick={() => handleBotAction("restart")}
            className="cyber-button-secondary flex items-center space-x-2"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RotateCcw className="w-4 h-4" />
            <span>Restart Bot</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="cyber-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-cyber-light/60">Total Messages</p>
              <p className="text-3xl font-bold text-cyber-blue">
                {stats.total_messages.toLocaleString()}
              </p>
            </div>
            <MessageSquare className="w-8 h-8 text-cyber-blue/60" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="cyber-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-cyber-light/60">Active Sessions</p>
              <p className="text-3xl font-bold text-cyber-green">
                {stats.active_sessions}
              </p>
            </div>
            <Activity className="w-8 h-8 text-cyber-green/60" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="cyber-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-cyber-light/60">Total Users</p>
              <p className="text-3xl font-bold text-cyber-magenta">
                {stats.total_users}
              </p>
            </div>
            <Users className="w-8 h-8 text-cyber-magenta/60" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="cyber-card"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-cyber-light/60">Recent Activity</p>
              <p className="text-3xl font-bold text-cyber-yellow">
                {stats.recent_activity}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-cyber-yellow/60" />
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
        className="cyber-card"
      >
        <h3 className="text-xl font-orbitron font-bold text-cyber-blue mb-4">
          Quick Actions
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <motion.button
            className="cyber-button-secondary p-4 text-left group"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Zap className="w-6 h-6 text-cyber-blue mb-2 group-hover:text-cyber-magenta transition-colors" />
            <h4 className="font-semibold text-cyber-light">Send Message</h4>
            <p className="text-sm text-cyber-light/60">Send manual chat message</p>
          </motion.button>

          <motion.button
            className="cyber-button-secondary p-4 text-left group"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Activity className="w-6 h-6 text-cyber-green mb-2 group-hover:text-cyber-blue transition-colors" />
            <h4 className="font-semibold text-cyber-light">View Logs</h4>
            <p className="text-sm text-cyber-light/60">Check recent activity</p>
          </motion.button>

          <motion.button
            className="cyber-button-secondary p-4 text-left group"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <AlertCircle className="w-6 h-6 text-cyber-yellow mb-2 group-hover:text-cyber-magenta transition-colors" />
            <h4 className="font-semibold text-cyber-light">System Health</h4>
            <p className="text-sm text-cyber-light/60">Check system status</p>
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}