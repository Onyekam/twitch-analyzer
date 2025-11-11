import React, { useEffect, useState } from "react";
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Container,
  Card,
  CardContent,
  Box,
  CircularProgress,
  Button,
  Stack,
  Chip,
  Alert
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

type Props = {
  name: string;
  apiBase: string;
  onBack: () => void;
};

type GameDetailsData = {
  game_name: string;
  times_played?: number;
  image?: string;
  summary?: string;
  viewers?: number;
};

const GameDetails: React.FC<Props> = ({ name, apiBase, onBack }) => {
  const [data, setData] = useState<GameDetailsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Try an explicit game endpoint first, then fall back to most_streamed list
    const tryFetch = async () => {
      try {
        if (apiBase) {
          const gameUrl = `${apiBase.replace(/\/$/, "")}/games/${encodeURIComponent(name)}`;
          const res = await fetch(gameUrl);
          if (res.ok) {
            const json = await res.json();
            // Expecting { data: { ... } } or raw object
            const payload = json?.data || json;
            if (payload) {
              setData({
                game_name: payload.game_name || name,
                times_played: payload.times_played,
                image: payload.image,
                summary: payload.summary,
                viewers: payload.viewers,
              });
              setLoading(false);
              return;
            }
          }
        }

        // Fallback: fetch top list and find by name
        if (apiBase) {
          const listUrl = `${apiBase.replace(/\/$/, "")}/most_streamed/top5`;
          const res2 = await fetch(listUrl);
          if (res2.ok) {
            const json2 = await res2.json();
            const arr = Array.isArray(json2?.data) ? json2.data : json2;
            const found = Array.isArray(arr)
              ? arr.find((g: Record<string, unknown>) => String((g as Record<string, unknown>)["game_name"]) === name)
              : null;
            if (found) {
              setData({
                game_name: found.game_name,
                times_played: found.times_played,
                image: found.image,
              });
              setLoading(false);
              return;
            }
          }
        }

        // Last resort: show the name only
        setData({ game_name: name });
        setLoading(false);
      } catch (err: unknown) {
        console.error(err);
        setError(String(err));
        setLoading(false);
      }
    };

    tryFetch();
  }, [name, apiBase]);

  const imageUrl = data?.image || `https://static-cdn.jtvnw.net/ttv-boxart/${encodeURIComponent(name)}-285x380.jpg`;

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: (t) => t.palette.background.default }}>
      <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Toolbar>
          <IconButton edge="start" onClick={onBack}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" sx={{ ml: 1, fontWeight: 700 }}>{name}</Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 4 }}>
        {error && <Alert severity="error">{error}</Alert>}

        <Card variant="outlined">
          <CardContent>
            {loading ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Stack direction={{ xs: "column", sm: "row" }} spacing={3}>
                <Box component="img" src={imageUrl} alt={name} sx={{ width: 200, height: 266, borderRadius: 1, objectFit: "cover" }} />

                <Box sx={{ flex: 1 }}>
                  <Typography variant="h5" gutterBottom sx={{ textTransform: "capitalize" }}>{data?.game_name}</Typography>
                  <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    {typeof data?.times_played !== 'undefined' && (
                      <Chip label={`Times streamed: ${data!.times_played}`} />
                    )}
                    {typeof data?.viewers !== 'undefined' && (
                      <Chip label={`Viewers: ${data!.viewers}`} color="primary" />
                    )}
                  </Stack>

                  <Typography color="text.secondary" sx={{ mb: 2 }}>{data?.summary || 'No description available.'}</Typography>

                  <Button variant="contained" onClick={onBack}>Back to list</Button>
                </Box>
              </Stack>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default GameDetails;
