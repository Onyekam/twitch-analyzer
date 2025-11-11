import React, { useEffect, useMemo, useState } from "react";
import {
  Box,
  Container,
  Card,
  CardHeader,
  CardContent,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  CircularProgress,
  Typography,
  TextField,
  InputAdornment,
  Button,
  Stack,
  import React, { useEffect, useMemo, useState } from "react";
  import {
    Box,
    Container,
    Card,
    CardHeader,
    CardContent,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    CircularProgress,
    Typography,
    TextField,
    InputAdornment,
    Button,
    Stack,
    Pagination,
  } from "@mui/material";
  import SearchIcon from "@mui/icons-material/Search";

  type Props = {
    apiBase: string;
    onBack?: () => void;
  };

  type GameRow = { game_name: string; image?: string; summary?: string };

  const LETTERS = ["All", ...Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i)), "#"];
  const PAGE_SIZE = 25;

  const GamesList: React.FC<Props> = ({ apiBase }) => {
    const [rows, setRows] = useState<GameRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [query, setQuery] = useState("");
    const [letter, setLetter] = useState<string>("All");
    const [page, setPage] = useState<number>(1);

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

    const filteredByLetter = useMemo(() => {
      const q = (query || "").trim().toLowerCase();
      return rows.filter((r) => {
        const name = (r.game_name || "").toLowerCase();
        if (q && !name.includes(q)) return false;
        if (letter === "All") return true;
        if (letter === "#") return !/^[a-zA-Z]/.test(name.charAt(0));
        return name.startsWith(letter.toLowerCase());
      });
    }, [rows, letter, query]);

    const totalPages = Math.max(1, Math.ceil(filteredByLetter.length / PAGE_SIZE));

    const pageSlice = useMemo(() => {
      const start = (page - 1) * PAGE_SIZE;
      return filteredByLetter.slice(start, start + PAGE_SIZE);
    }, [filteredByLetter, page]);

    useEffect(() => setPage(1), [letter, query]);

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

              <Stack direction="row" spacing={1} sx={{ mb: 2, overflowX: "auto", pb: 1 }}>
                {LETTERS.map((L) => (
                  <Button key={L} size="small" variant={L === letter ? "contained" : "outlined"} onClick={() => setLetter(L)}>
                    {L}
                  </Button>
                ))}
              </Stack>

              {loading ? (
                <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <>
                  <List>
                    {pageSlice.map((g) => {
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

                  <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
                    <Pagination count={totalPages} page={page} onChange={(_, p) => setPage(p)} color="primary" />
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Container>
      </Box>
    );
  };

  export default GamesList;
