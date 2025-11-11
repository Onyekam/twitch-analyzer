import React, { useEffect, useState } from "react";
import { Box, Container, Card, CardHeader, CardContent, List, ListItem, ListItemButton, ListItemText, CircularProgress, Typography, TextField, InputAdornment } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

type Props = {
  apiBase: string;
  onBack?: () => void;
};

type GameRow = { game_name: string; image?: string; summary?: string };

const GamesList: React.FC<Props> = ({ apiBase }) => {
  const [rows, setRows] = useState<GameRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const url = `${apiBase.replace(/\/$/, "")}/games`;
    setLoading(true);
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((json) => {
        const arr = Array.isArray(json?.data) ? json.data : json;
        setRows(Array.isArray(arr) ? arr : []);
      })
      .catch((err) => {
        console.error(err);
        setRows([]);
      })
      .finally(() => setLoading(false));
  }, [apiBase]);

  const filtered = query ? rows.filter((r) => (r.game_name || "").toLowerCase().includes(query.toLowerCase())) : rows;

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: (t) => t.palette.background.default }}>
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Card variant="outlined">
          <CardHeader title="All Games" subheader={`Total: ${rows.length}`} />
          <CardContent>
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
              sx={{ mb: 2 }}
            />

            {loading ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List>
                {filtered.map((g) => {
                  const img = g.image || `https://static-cdn.jtvnw.net/ttv-boxart/${encodeURIComponent(g.game_name)}-85x120.jpg`;
                  return (
                    <ListItem key={g.game_name} disablePadding>
                      <ListItemButton onClick={() => (window.location.hash = `#/game/${encodeURIComponent(g.game_name)}`)} sx={{ alignItems: "center" }}>
                        <Box component="img" src={img} alt={g.game_name} sx={{ width: 48, height: 64, objectFit: "cover", borderRadius: 1, mr: 2 }} />
                        <ListItemText primary={<Typography sx={{ textTransform: "capitalize" }}>{g.game_name}</Typography>} />
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </List>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default GamesList;
