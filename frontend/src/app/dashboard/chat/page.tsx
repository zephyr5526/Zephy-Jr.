"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  User, 
  Bot, 
  Crown, 
  Shield,
  Filter,
  Download,
  RefreshCw
} from "lucide-react";

interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  display_name?: string;
  message: string;
  is_admin: boolean;
  is_moderator: boolean;
  is_owner: boolean;
  timestamp: string;
  processed: boolean;
  response?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [streamId, setStreamId] = useState("O-sJ8qOvNr4");
  const [filter, setFilter] = useState<"all" | "admin" | "users">("all");
  const [loading, setLoading] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Simulate real-time messages
  useEffect(() => {
    const sampleMessages: ChatMessage[] = [
      {
        id: "1",
        user_id: "admin",
        username: "Admin",
        message: "Welcome to the stream!",
        is_admin: true,
        is_moderator: false,
        is_owner: true,
        timestamp: new Date(Date.now() - 300000).toISOString(),
        processed: true,
        response: "Welcome message sent",
      },
      {
        id: "2",
        user_id: "user1",
        username: "Viewer123",
        message: "Hey Zephy! How are you?",
        is_admin: false,
        is_moderator: false,
        is_owner: false,
        timestamp: new Date(Date.now() - 240000).toISOString(),
        processed: true,
        response: "Hey there! I'm doing great, thanks for asking! 😊",
      },
      {
        id: "3",
        user_id: "user2",
        username: "GamerPro",
        message: "!start",
        is_admin: false,
        is_moderator: false,
        is_owner: false,
        timestamp: new Date(Date.now() - 180000).toISOString(),
        processed: true,
        response: "Started your focus session! Let's go! 💪",
      },
      {
        id: "4",
        user_id: "user3",
        username: "StudyBuddy",
        message: "!quiz",
        is_admin: false,
        is_moderator: false,
        is_owner: false,
        timestamp: new Date(Date.now() - 120000).toISOString(),
        processed: true,
        response: "What is the capital of France?\nOptions:\n1. London\n2. Berlin\n3. Paris\n4. Madrid\n(Reply with !answer <number>)",
      },
      {
        id: "5",
        user_id: "user4",
        username: "NewViewer",
        message: "First time here!",
        is_admin: false,
        is_moderator: false,
        is_owner: false,
        timestamp: new Date(Date.now() - 60000).toISOString(),
        processed: true,
        response: "Welcome to the stream! Hope you enjoy your stay! 🎉",
      },
    ];

    setMessages(sampleMessages);

    // Simulate new messages
    const interval = setInterval(() => {
      const newMsg: ChatMessage = {
        id: Date.now().toString(),
        user_id: `user${Math.floor(Math.random() * 1000)}`,
        username: `Viewer${Math.floor(Math.random() * 1000)}`,
        message: `Random message ${Math.floor(Math.random() * 1000)}`,
        is_admin: false,
        is_moderator: false,
        is_owner: false,
        timestamp: new Date().toISOString(),
        processed: false,
      };
      
      setMessages(prev => [...prev, newMsg]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, autoScroll]);

  const filteredMessages = messages.filter(msg => {
    if (filter === "admin") return msg.is_admin || msg.is_moderator || msg.is_owner;
    if (filter === "users") return !msg.is_admin && !msg.is_moderator && !msg.is_owner;
    return true;
  });

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const sentMessage: ChatMessage = {
        id: Date.now().toString(),
        user_id: "admin",
        username: "Admin",
        message: newMessage,
        is_admin: true,
        is_moderator: false,
        is_owner: true,
        timestamp: new Date().toISOString(),
        processed: true,
        response: "Message sent successfully",
      };
      
      setMessages(prev => [...prev, sentMessage]);
      setNewMessage("");
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setLoading(false);
    }
  };

  const getMessageIcon = (message: ChatMessage) => {
    if (message.is_owner) return <Crown className="w-4 h-4 text-cyber-yellow" />;
    if (message.is_moderator) return <Shield className="w-4 h-4 text-cyber-blue" />;
    if (message.is_admin) return <User className="w-4 h-4 text-cyber-green" />;
    return <User className="w-4 h-4 text-cyber-light/60" />;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-orbitron font-bold text-cyber-blue">
            Chat Management
          </h1>
          <p className="text-cyber-light/60 mt-1">
            Monitor and manage live chat messages
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-cyber-green rounded-full cyber-pulse"></div>
            <span className="text-sm text-cyber-light/60">Live</span>
          </div>
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              autoScroll 
                ? "bg-cyber-blue/20 text-cyber-blue border border-cyber-blue/30" 
                : "bg-cyber-gray/50 text-cyber-light/60"
            }`}
          >
            Auto-scroll
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="cyber-card">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm text-cyber-light/60 mb-1">Stream ID</label>
              <input
                type="text"
                value={streamId}
                onChange={(e) => setStreamId(e.target.value)}
                className="cyber-input w-48"
                placeholder="Video ID"
              />
            </div>
            
            <div>
              <label className="block text-sm text-cyber-light/60 mb-1">Filter</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as "all" | "admin" | "users")}
                className="cyber-input w-32"
              >
                <option value="all">All</option>
                <option value="admin">Admins</option>
                <option value="users">Users</option>
              </select>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="cyber-button-secondary flex items-center space-x-2">
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            <button className="cyber-button-secondary flex items-center space-x-2">
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="cyber-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-orbitron font-bold text-cyber-blue">
            Live Chat
          </h3>
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-cyber-light/60" />
            <span className="text-sm text-cyber-light/60">
              {filteredMessages.length} messages
            </span>
          </div>
        </div>

        <div className="h-96 overflow-y-auto space-y-3 pr-2">
          <AnimatePresence>
            {filteredMessages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className={`p-4 rounded-lg border ${
                  message.is_admin || message.is_moderator || message.is_owner
                    ? "bg-cyber-blue/5 border-cyber-blue/20"
                    : "bg-cyber-gray/20 border-cyber-gray/30"
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getMessageIcon(message)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-semibold text-cyber-light">
                        {message.display_name || message.username}
                      </span>
                      {message.is_owner && (
                        <span className="px-2 py-0.5 bg-cyber-yellow/20 text-cyber-yellow text-xs rounded">
                          Owner
                        </span>
                      )}
                      {message.is_moderator && (
                        <span className="px-2 py-0.5 bg-cyber-blue/20 text-cyber-blue text-xs rounded">
                          Mod
                        </span>
                      )}
                      {message.is_admin && (
                        <span className="px-2 py-0.5 bg-cyber-green/20 text-cyber-green text-xs rounded">
                          Admin
                        </span>
                      )}
                      <span className="text-xs text-cyber-light/40">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    
                    <p className="text-cyber-light/80 mb-2">{message.message}</p>
                    
                    {message.response && (
                      <div className="bg-cyber-dark/50 p-3 rounded border-l-2 border-cyber-blue/50">
                        <div className="flex items-center space-x-2 mb-1">
                          <Bot className="w-4 h-4 text-cyber-blue" />
                          <span className="text-sm font-medium text-cyber-blue">Bot Response</span>
                        </div>
                        <p className="text-sm text-cyber-light/70">{message.response}</p>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Send Message */}
      <div className="cyber-card">
        <h3 className="text-xl font-orbitron font-bold text-cyber-blue mb-4">
          Send Message
        </h3>
        
        <div className="flex space-x-3">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
            className="cyber-input flex-1"
            placeholder="Type your message here..."
            disabled={loading}
          />
          <motion.button
            onClick={handleSendMessage}
            disabled={loading || !newMessage.trim()}
            className="cyber-button flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: loading ? 1 : 1.05 }}
            whileTap={{ scale: loading ? 1 : 0.95 }}
          >
            {loading ? (
              <div className="cyber-loading w-4 h-4 border-2 border-cyber-black border-t-transparent rounded-full"></div>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Send</span>
              </>
            )}
          </motion.button>
        </div>
      </div>
    </div>
  );
}