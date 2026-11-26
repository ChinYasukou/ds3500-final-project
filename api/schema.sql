CREATE TABLE IF NOT EXISTS teams (
    season TEXT NOT NULL,
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL,
    conference TEXT NOT NULL CHECK (conference IN ('East', 'West')),
    wins INTEGER NOT NULL CHECK (wins >= 0),
    losses INTEGER NOT NULL CHECK (losses >= 0),
    PRIMARY KEY (season, team_id)
);

-- One combined regular-season record per player, including traded players.
CREATE TABLE IF NOT EXISTS players (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    games_played INTEGER NOT NULL CHECK (games_played > 0),
    points_per_game REAL NOT NULL CHECK (points_per_game >= 0),
    rebounds_per_game REAL NOT NULL CHECK (rebounds_per_game >= 0),
    assists_per_game REAL NOT NULL CHECK (assists_per_game >= 0),
    PRIMARY KEY (season, player_id)
);
