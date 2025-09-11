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
  Button,
  Alert,
  List,
  ListItem,
  ListItemText
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import RefreshIcon from "@mui/icons-material/Refresh";
import BarChartIcon from "@mui/icons-material/BarChart";
import DataObjectIcon from "@mui/icons-material/DataObject";

// Use FastAPI/Vite proxy in dev, or override with VITE_API_BASE for preview/prod
const API_BASE = (import.meta as any).env?.VITE_API_BASE || "";
const API_URL = `${API_BASE}/most_streamed/top5`;

type MostStreamedRow = { game_name: string; times_played: number };

const App: React.FC = () => {
  const [rows, setRows] = useState<MostStreamedRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    fetch(API_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        const arr = Array.isArray(data?.data) ? (data.data as MostStreamedRow[]) : [];
        setRows(arr);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(String(err));
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filtered = useMemo(() => {
    if (!query) return rows;
    const q = query.toLowerCase();
    return rows.filter((r) => String(r.game_name || "").toLowerCase().includes(q));
  }, [rows, query]);

  const listItems = useMemo(
    () => filtered.map((r) => ({ name: r.game_name || "Unknown", count: r.times_played })),
    [filtered]
  );

  const numberFmt = useMemo(() => new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }), []);

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
            placeholder="Search games…"
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
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load data from {API_URL}. {error}
          </Alert>
        )}
        <Box sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "2fr 1fr" },
          gap: 3
        }}>
          <Card variant="outlined">
            <CardHeader title="Most Streamed Games" subheader={`${filtered.length} games`} />
            <CardContent>
              {loading ? (
                <Box sx={{ py: 6, display: "flex", justifyContent: "center" }}>
                  <CircularProgress />
                </Box>
              ) : listItems.length === 0 ? (
                <Typography color="text.secondary">No data to display.</Typography>
              ) : (
                <Box>
                  <List>
                    {listItems.map((item, idx) => (
                      <ListItem key={item.name} divider secondaryAction={<Typography color="primary" fontWeight={700}>{numberFmt.format(item.count)}</Typography>}>
                        <ListItemText primary={<Typography sx={{ textTransform: 'capitalize' }}>{`${idx + 1}. ${item.name}`}</Typography>} secondary="Times streamed" />
                      </ListItem>
                    ))}
                  </List>
                </Box>

                // Chart preserved for future use:
                // <Box sx={{ height: 360 }}>
                //   <ResponsiveContainer width="100%" height="100%">
                //     <BarChart data={chartData}>
                //       <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-20} height={60} tickMargin={8} />
                //       <YAxis allowDecimals={false} />
                //       <Tooltip />
                //       <Bar dataKey="count" fill="#6366F1" radius={[6, 6, 0, 0]} />
                //     </BarChart>
                //   </ResponsiveContainer>
                // </Box>
              )}
            </CardContent>
          </Card>

          <Stack spacing={3}>
            <Card variant="outlined">
              <CardHeader title="Summary" />
              <CardContent>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Chip label={`Games: ${filtered.length}`} />
                  <Chip color="primary" label={`Total Streams Today: ${numberFmt.format(filtered.reduce((a, r) => a + (r.times_played || 0), 0))}`} />
                </Stack>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardHeader avatar={<DataObjectIcon />} title="Raw Data" />
              <CardContent>
                <Paper variant="outlined" sx={{ p: 1.5, maxHeight: 240, overflow: "auto" }}>
                  <pre style={{ margin: 0 }}>
                    {JSON.stringify(filtered, null, 2)}
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
            Built with Material UI
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