import { motion } from "framer-motion";
import { ReactNode } from "react";

export function AnimatedCard({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay, ease: "easeOut" }}
      whileHover={{ scale: 1.01 }}
      className={`bg-card text-card-foreground rounded-xl border border-border/50 shadow-sm p-6 ${className}`}
    >
      {children}
    </motion.div>
  );
}
