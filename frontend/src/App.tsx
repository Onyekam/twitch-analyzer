// src/App.tsx
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const API_URL = "https://your-flask-backend.com/streams"; // Replace with your Render URL

const App: React.FC = () => {
  const [streamData, setStreamData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(API_URL)
      .then((res) => res.json())
      .then((data) => {
        setStreamData(data.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const topGames = streamData.reduce((acc: any, stream: any) => {
    const game = stream.game_name;
    acc[game] = (acc[game] || 0) + 1;
    return acc;
  }, {});

  const chartData = Object.entries(topGames).map(([name, count]) => ({ name, count }));

  return (
    <main className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Twitch Stream Analytics</h1>
      {loading ? (
        <p>Loading data...</p>
      ) : (
        <>
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-2">Top Streamed Games</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-45} textAnchor="end" height={100} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#6366F1" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-2">Raw Stream Data</h2>
              <pre className="text-xs whitespace-pre-wrap overflow-auto">
                {JSON.stringify(streamData.slice(0, 5), null, 2)}
              </pre>
            </CardContent>
          </Card>
        </>
      )}
    </main>
  );
};

export default App;