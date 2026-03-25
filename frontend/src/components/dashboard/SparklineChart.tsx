import { LineChart, Line, ResponsiveContainer } from "recharts";

interface Props {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export default function SparklineChart({
  data,
  color = "#3b82f6",
  width = 80,
  height = 30,
}: Props) {
  if (!data || data.length < 2) return null;
  const chartData = data.map((v, i) => ({ i, v }));

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="v"
            stroke={color}
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
