import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

const COLORS = [
  "hsl(168, 35%, 42%)",
  "hsl(200, 45%, 50%)",
  "hsl(260, 35%, 55%)",
  "hsl(320, 40%, 55%)",
  "hsl(40, 50%, 55%)",
  "hsl(120, 35%, 45%)",
  "hsl(0, 45%, 55%)",
  "hsl(180, 40%, 45%)",
];

export function AllocationChart({ data }: { data: { name: string; value: number }[] }) {
  if (!data.length) return null;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
          nameKey="name"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
            fontSize: "13px",
          }}
          formatter={(v: number) => [`${v.toFixed(1)}%`, "Allocation"]}
        />
        <Legend wrapperStyle={{ fontSize: "12px" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
