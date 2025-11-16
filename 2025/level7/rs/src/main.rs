use fxhash::FxHashMap;
use quadtree_rs::{Quadtree, area::AreaBuilder, point::Point};
use rayon::prelude::*;
use std::collections::BinaryHeap;
use std::io::{self, BufRead};
use std::time::Instant;

fn apply_acc(v: i8, dv: i8) -> i8 {
    if v == 0 {
        return dv * 5;
    }
    if (v + dv).abs() == 0 {
        return v;
    }
    if (v + dv).abs() == 6 {
        return 0;
    }

    v + dv
}

const K: i16 = 4;

type State = (i16, i16, i8, i8, u8, u8);

#[derive(Copy, Clone, Debug)]
struct GridEntry {
    time: u16,
}

impl GridEntry {
    fn new() -> Self {
        Self { time: u16::MAX }
    }
}

struct QueueItem {
    heuristic: u16,
    time: u16,
    state: State,
    prev_state: Option<State>,
}

impl QueueItem {
    fn new(heuristic: u16, time: u16, state: State, prev_state: Option<State>) -> Self {
        Self {
            heuristic,
            time,
            state,
            prev_state,
        }
    }
}

impl PartialEq for QueueItem {
    fn eq(&self, other: &Self) -> bool {
        self.heuristic == other.heuristic && self.time == other.time && self.state == other.state
    }
}

impl Eq for QueueItem {}

impl PartialOrd for QueueItem {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for QueueItem {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.heuristic
            .cmp(&other.heuristic)
            .reverse()
            .then(self.time.cmp(&other.time).reverse())
    }
}

fn solve(
    i: usize,
    x_target: i16,
    y_target: i16,
    asteroids: &[(i16, i16)],
    max_t: u16,
) -> Result<(Vec<i8>, Vec<i8>), String> {
    let start = Instant::now();

    let mut asteroid_tree = Quadtree::<i16, ()>::new_with_anchor(
        Point {
            x: i16::MIN,
            y: i16::MIN,
        },
        14,
    );

    for (x, y) in asteroids {
        asteroid_tree.insert_pt(
            Point {
                x: *x + 1,
                y: *y + 1,
            },
            (),
        );
    }

    let mut items = vec![(x_target, y_target), (0, 0)];
    items.extend(asteroids);

    let bounding_box = (
        items.iter().map(|(x, _)| *x).min().unwrap() - K,
        items.iter().map(|(x, _)| *x).max().unwrap() + K,
        items.iter().map(|(_, y)| *y).min().unwrap() - K,
        items.iter().map(|(_, y)| *y).max().unwrap() + K,
    );

    let x_range = bounding_box.0..=bounding_box.1;
    let y_range = bounding_box.2..=bounding_box.3;

    let state = (0, 0, 0, 0, 0, 0);

    // Using BinaryHeap with Reverse for min-heap behavior
    let mut queue: BinaryHeap<QueueItem> = BinaryHeap::new();
    queue.push(QueueItem::new(0, 2, state, None));

    let mut grid: FxHashMap<State, GridEntry> = FxHashMap::default();
    grid.insert(state, GridEntry::new());

    let mut predecessors: FxHashMap<State, Option<State>> = FxHashMap::default();

    while let Some(QueueItem {
        time,
        state,
        prev_state,
        ..
    }) = queue.pop()
    {
        let grid_entry = grid.entry(state).or_insert_with(GridEntry::new);
        if time > grid_entry.time {
            continue;
        }

        let (x, y, v_x, v_y, tick_x, tick_y) = state;

        let builder = AreaBuilder::default()
            .anchor(Point { x, y })
            .dimensions((3, 3))
            .build();

        if asteroid_tree
            .query(unsafe { builder.unwrap_unchecked() })
            .next()
            .is_some()
        {
            continue;
        }

        grid_entry.time = time;
        predecessors.insert(state, prev_state);

        if x == x_target && y == y_target && v_x == 0 && v_y == 0 {
            let mut moves_x = vec![0];
            let mut moves_y = vec![0];

            let mut current_state = state;
            while let Some(Some(prev_state)) = predecessors.get(&current_state) {
                if current_state.2 != prev_state.2 || current_state.4 >= prev_state.4 {
                    moves_x.push(prev_state.2);
                }

                if current_state.3 != prev_state.3 || current_state.5 >= prev_state.5 {
                    moves_y.push(prev_state.3);
                }

                current_state = *prev_state;
            }
            moves_x.reverse();
            moves_y.reverse();

            let elapsed = start.elapsed();
            eprintln!(
                "Done {} in {:?} in {} steps out of {} allowed",
                i, elapsed, time, max_t
            );

            return Ok((moves_x, moves_y));
        }

        let elapsed = tick_x.min(tick_y) + 1;

        let x_changes = if let Some(new_tick_x) = tick_x.checked_sub(elapsed) {
            &[(x, v_x, new_tick_x)] as &[(i16, i8, u8)]
        } else {
            let new_x = x + v_x.signum() as i16;
            &[
                (
                    new_x,
                    apply_acc(v_x, -1),
                    apply_acc(v_x, -1).unsigned_abs().saturating_sub(1),
                ),
                (
                    new_x,
                    apply_acc(v_x, 0),
                    apply_acc(v_x, 0).unsigned_abs().saturating_sub(1),
                ),
                (
                    new_x,
                    apply_acc(v_x, 1),
                    apply_acc(v_x, 1).unsigned_abs().saturating_sub(1),
                ),
            ]
        };

        let y_changes = if let Some(new_tick_y) = tick_y.checked_sub(elapsed) {
            &[(y, v_y, new_tick_y)] as &[(i16, i8, u8)]
        } else {
            let new_y = y + v_y.signum() as i16;
            &[
                (
                    new_y,
                    apply_acc(v_y, -1),
                    apply_acc(v_y, -1).unsigned_abs().saturating_sub(1),
                ),
                (
                    new_y,
                    apply_acc(v_y, 0),
                    apply_acc(v_y, 0).unsigned_abs().saturating_sub(1),
                ),
                (
                    new_y,
                    apply_acc(v_y, 1),
                    apply_acc(v_y, 1).unsigned_abs().saturating_sub(1),
                ),
            ]
        };

        for ((new_x, new_v_x, new_tick_x), (new_y, new_v_y, new_tick_y)) in
            itertools::iproduct!(x_changes, y_changes)
        {
            if !(x_range.contains(new_x) && y_range.contains(new_y)) {
                continue;
            }

            let new_time = time + elapsed as u16;
            if new_time > max_t {
                continue;
            }

            let new_state = (*new_x, *new_y, *new_v_x, *new_v_y, *new_tick_x, *new_tick_y);
            let new_entry = grid.entry(new_state).or_insert_with(GridEntry::new);

            if new_time >= new_entry.time {
                continue;
            }

            new_entry.time = new_time;

            let new_heuristic = new_time
                + ((new_x - x_target).unsigned_abs() * new_v_x.unsigned_abs() as u16)
                    .max((new_y - y_target).unsigned_abs() * new_v_y.unsigned_abs() as u16);

            queue.push(QueueItem {
                time: new_time,
                state: new_state,
                prev_state,
                heuristic: new_heuristic,
            });
        }
    }

    Err("No solution".to_string())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();

    let n: usize = lines.next().unwrap()?.parse()?;

    let mut xs = Vec::new();
    let mut ys = Vec::new();
    let mut asteroids_list = Vec::new();
    let mut ts = Vec::new();

    for _ in 0..n {
        let line = lines.next().unwrap()?;
        let parts: Vec<&str> = line.split_whitespace().collect();
        let xy = parts[0];
        let t = parts[1];

        let coords: Vec<i16> = xy.split(',').map(|s| s.parse().unwrap()).collect();
        let x = coords[0];
        let y = coords[1];

        let _: usize = lines.next().unwrap()?.parse()?;

        let asteroid_line = lines.next().unwrap()?;
        let mut asteroids = Vec::new();

        for asteroid_str in asteroid_line.split_whitespace() {
            let asteroid_coords: Vec<i16> = asteroid_str
                .split(',')
                .map(|s| s.parse().unwrap())
                .collect();
            asteroids.push((asteroid_coords[0], asteroid_coords[1]));
        }

        xs.push(x);
        ys.push(y);
        asteroids_list.push(asteroids);
        ts.push(t.parse()?);
    }

    // Process in parallel using rayon
    let results: Vec<_> = (0..n)
        .into_par_iter()
        .map(|i| solve(i, xs[i], ys[i], &asteroids_list[i], ts[i]))
        .collect();

    // Output results in order
    for (i, result) in results.into_iter().enumerate() {
        match result {
            Ok((moves_x, moves_y)) => {
                println!(
                    "{}",
                    moves_x
                        .iter()
                        .map(|x| x.to_string())
                        .collect::<Vec<_>>()
                        .join(" ")
                );
                println!(
                    "{}",
                    moves_y
                        .iter()
                        .map(|y| y.to_string())
                        .collect::<Vec<_>>()
                        .join(" ")
                );
                println!();
            }
            Err(e) => {
                eprintln!("Error solving case {}: {}", i, e);
                return Err(e.into());
            }
        }
    }

    Ok(())
}
