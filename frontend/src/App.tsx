// src/App.tsx
import React, { useEffect, useMemo, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Card,
  CardHeader,
  CardContent,
  IconButton,
  TextField,
  InputAdornment,
  CircularProgress,
  Box,
  Stack,
  Divider,
  Chip,
  Tooltip as MuiTooltip,
  Paper,
  Link,
  Button
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import RefreshIcon from "@mui/icons-material/Refresh";
import BarChartIcon from "@mui/icons-material/BarChart";
import DataObjectIcon from "@mui/icons-material/DataObject";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

const API_URL = "https://your-flask-backend.com/streams"; // Replace with your Render URL

const App: React.FC = () => {
  const [streamData, setStreamData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const fetchData = () => {
    setLoading(true);
    fetch(API_URL)
      .then((res) => res.json())
      .then((data) => {
        setStreamData(Array.isArray(data?.data) ? data.data : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filtered = useMemo(() => {
    if (!query) return streamData;
    const q = query.toLowerCase();
    return streamData.filter((s) =>
      String(s?.game_name || "").toLowerCase().includes(q) ||
      String(s?.user_name || "").toLowerCase().includes(q)
    );
  }, [streamData, query]);

  const topGamesMap = useMemo(() => {
    return filtered.reduce((acc: any, stream: any) => {
      const game = stream?.game_name || "Unknown";
      acc[game] = (acc[game] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [filtered]);

  const chartData = useMemo(
    () => Object.entries(topGamesMap).map(([name, count]) => ({ name, count })),
    [topGamesMap]
  );

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: (t) => t.palette.background.default }}>
      <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Toolbar sx={{ gap: 2 }}>
          <BarChartIcon color="primary" />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            Twitch Stream Analytics
          </Typography>
          <TextField
            size="small"
            placeholder="Search games or streamers…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          <MuiTooltip title="Refresh data">
            <span>
              <IconButton onClick={fetchData} disabled={loading}>
                {loading ? <CircularProgress size={20} /> : <RefreshIcon />} 
              </IconButton>
            </span>
          </MuiTooltip>
        </Toolbar>
      </AppBar>

      <Container maxWidth={false} sx={{ py: 4 }}>
        <Box sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "2fr 1fr" },
          gap: 3
        }}>
          <Card variant="outlined">
            <CardHeader title="Top Streamed Games" subheader={`${filtered.length} streams`} />
            <CardContent>
              {loading ? (
                <Box sx={{ py: 6, display: "flex", justifyContent: "center" }}>
                  <CircularProgress />
                </Box>
              ) : chartData.length === 0 ? (
                <Typography color="text.secondary">No data to display.</Typography>
              ) : (
                <Box sx={{ height: 360 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-20} height={60} tickMargin={8} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#6366F1" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </CardContent>
          </Card>

          <Stack spacing={3}>
            <Card variant="outlined">
              <CardHeader title="Summary" />
              <CardContent>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Chip label={`Games: ${Object.keys(topGamesMap).length}`} />
                  <Chip color="primary" label={`Streams: ${filtered.length}`} />
                </Stack>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardHeader avatar={<DataObjectIcon />} title="Raw Stream Data (first 10)" />
              <CardContent>
                <Paper variant="outlined" sx={{ p: 1.5, maxHeight: 240, overflow: "auto" }}>
                  <pre style={{ margin: 0 }}>
                    {JSON.stringify(filtered.slice(0, 10), null, 2)}
                  </pre>
                </Paper>
              </CardContent>
            </Card>

            <Paper variant="outlined" sx={{ p: 2, textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">
                Backend URL: <Link href={API_URL} target="_blank" rel="noopener">{API_URL}</Link>
              </Typography>
            </Paper>
          </Stack>
        </Box>

        <Divider sx={{ my: 4 }} />
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="body2" color="text.secondary">
            Built with Material UI and Recharts
          </Typography>
          <Button variant="contained" href="#top">
            Back to top
          </Button>
        </Stack>
      </Container>
    </Box>
  );
};

export default App;