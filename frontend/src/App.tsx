// src/App.tsx
import React, { useEffect, useMemo, useState } from "react";
import GameDetails from "./pages/GameDetails";
import GamesList from "./pages/GamesList";
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
  //Paper,
  //Link,
  Button,
  Alert,
  List,
  ListItem,
  ListItemButton,
  ListItemText
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import RefreshIcon from "@mui/icons-material/Refresh";
import BarChartIcon from "@mui/icons-material/BarChart";
import ListIcon from "@mui/icons-material/List";
//import DataObjectIcon from "@mui/icons-material/DataObject";

// Use FastAPI/Vite proxy in dev, or override with VITE_API_BASE for preview/prod
const API_BASE = (import.meta as any).env?.VITE_API_BASE || "";
const API_URL = `${API_BASE}/most_streamed/top5`;

type MostStreamedRow = { game_name: string; times_played: number; image?: string };

const App: React.FC = () => {
  const [rows, setRows] = useState<MostStreamedRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [hash, setHash] = useState<string>(window.location.hash || "");

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

  useEffect(() => {
    const onHash = () => setHash(window.location.hash || "");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const filtered = useMemo(() => {
    if (!query) return rows;
    const q = query.toLowerCase();
    return rows.filter((r) => String(r.game_name || "").toLowerCase().includes(q));
  }, [rows, query]);


  const numberFmt = useMemo(() => new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }), []);

  // Simple hash routing: #/game/<name>
  const gameNameFromHash = useMemo(() => {
    if (!hash) return null;
    const prefix = "#/game/";
    if (hash.startsWith(prefix)) {
      return decodeURIComponent(hash.slice(prefix.length));
    }
    return null;
  }, [hash]);

  const showGamesList = useMemo(() => hash === "#/games", [hash]);

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: (t) => t.palette.background.default }}>
      <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Toolbar sx={{ gap: 2 }}>
          <IconButton onClick={() => (window.location.hash = "")} aria-label="Home" size="small">
            <BarChartIcon color="primary" />
          </IconButton>
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
          <Button
            variant="outlined"
            size="small"
            href="#/games"
            startIcon={<ListIcon />}
            aria-label="All games"
          >
            All games
          </Button>
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

        {gameNameFromHash ? (
          <GameDetails name={gameNameFromHash} apiBase={API_BASE} onBack={() => (window.location.hash = "") } />
        ) : showGamesList ? (
          <GamesList apiBase={API_BASE} />
        ) : (
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
                ) : filtered.length === 0 ? (
                  <Typography color="text.secondary">No data to display.</Typography>
                ) : (
                  <Box>
                    <List>
  {filtered.map((r, idx) => {
    const imageUrl =
      r.image || 
        `https://static-cdn.jtvnw.net/ttv-boxart/${encodeURIComponent(r.game_name)}-85x120.jpg`; // Twitch box art fallback

    return (
      <ListItem key={r.game_name} divider sx={{ alignItems: "center" }}>
        <ListItemButton onClick={() => (window.location.hash = `#/game/${encodeURIComponent(r.game_name)}`)} sx={{ alignItems: "center" }}>
        <Typography variant="body2" sx={{ width: 24, color: "text.secondary", mr: 1 }}>
          {idx + 1}.
        </Typography>
  <Box
    component="img"
    src={imageUrl}
    alt={r.game_name}
    sx={{
      width: 40,
      height: 55,
      borderRadius: 1,
      objectFit: "cover",
      mr: 2,
      boxShadow: 1,
    }}
  />
  <ListItemText
    primary={<Typography sx={{ textTransform: "capitalize" }}>{r.game_name}</Typography>}
    secondary="Times streamed"
  />
  <Typography color="primary" fontWeight={700}>
    {numberFmt.format(r.times_played)}
  </Typography>
        </ListItemButton>
      </ListItem>
    );
  })}
</List>
                  </Box>
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

            </Stack> 
          </Box>
        )}

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