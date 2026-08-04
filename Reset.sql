-- =====================================================
-- FRONTLINES - RESET GAME
-- Resets the game back to Turn 1 while keeping all
-- static data (users, units, buildings, etc.)
-- =====================================================

-- Enable Unsafe Mode
SET SQL_SAFE_UPDATES = 0;

SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- CLEAR GAMEPLAY DATA
-- =====================================================

DELETE FROM turn_logs;
DELETE FROM battles;
DELETE FROM event_logs;
DELETE FROM nation_relations;
DELETE FROM nation_units;
DELETE FROM resource_history;
DELETE FROM trades;

DELETE FROM production_queue;
DELETE FROM building_queue;

DELETE FROM game_turns;

-- =====================================================
-- RESET GAME STATE
-- =====================================================

DELETE FROM game_state;

INSERT INTO game_state
(
    id,
    current_turn,
    game_paused,
    maintenance_mode
)
VALUES
(
    1,
    1,
    0,
    0
);

-- =====================================================
-- CREATE INITIAL TURN
-- =====================================================

INSERT INTO game_turns
(
    turn_id,
    started_at,
    processed_at,
    status,
    processing_time,
    notes
)
VALUES
(
    1,
    NOW(),
    NOW(),
    'Complete',
    0,
    'Initial game state'
);

SET FOREIGN_KEY_CHECKS = 1;

-- Disable Unsafe Mode
SET SQL_SAFE_UPDATES = 1;