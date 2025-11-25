use fxhash::FxHashMap;
use quadtree_rs::{Quadtree, area::AreaBuilder, point::Point};
use rayon::prelude::*;
use std::collections::BinaryHeap;
use std::collections::hash_map::Entry;
use std::io::{self, BufRead};
use std::time::Instant;

fn apply_acc(v: i8, dv: i8) -> i8 {
    if v == 0 {
        return dv * 5;
    }
    if v + dv == 0 {
        return v;
    }
    if (v + dv).abs() == 6 {
        return 0;
    }

    v + dv
}

type State = (i16, i16, i8, i8, u8, u8);

struct QueueItem {
    heuristic: u16,
    time: u16,
    state: State,
    prev_state: State,
}

impl QueueItem {
    fn new(heuristic: u16, time: u16, state: State, prev_state: State) -> Self {
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
            .then(self.time.cmp(&other.time))
            .reverse()
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

    let asteroid_tree = {
        // assume the grid fits within 2000x2000 centered around the origin
        let mut qtree = Quadtree::<i16, ()>::new_with_anchor(Point { x: -1000, y: -1000 }, 11);

        for (x, y) in asteroids {
            qtree.insert_pt(
                Point {
                    x: *x + 2,
                    y: *y + 2,
                },
                (),
            );
        }

        qtree
    };

    let state = (0, 0, 0, 0, 0, 0);

    let mut queue: BinaryHeap<QueueItem> = BinaryHeap::new();
    queue.push(QueueItem::new(0, 2, state, state));

    let mut grid: FxHashMap<State, u16> = FxHashMap::default();

    let mut predecessors: FxHashMap<State, State> = FxHashMap::default();

    while let Some(QueueItem {
        time,
        state,
        prev_state,
        ..
    }) = queue.pop()
    {
        let grid_entry = grid.entry(state);
        if let Entry::Occupied(old_time) = &grid_entry
            && time > *old_time.get()
        {
            continue;
        }

        let (x, y, v_x, v_y, tick_x, tick_y) = state;

        let builder = AreaBuilder::default()
            .anchor(Point { x, y })
            .dimensions((5, 5))
            .build();

        if asteroid_tree.query(builder.unwrap()).next().is_some() {
            continue;
        }

        grid_entry.insert_entry(time);
        predecessors.insert(state, prev_state);

        if x == x_target && y == y_target && v_x == 0 && v_y == 0 {
            let mut moves_x = vec![0];
            let mut moves_y = vec![0];

            let mut current_state = state;
            // walk through the predecessors, until we reach the start
            while let Some(prev_state) = predecessors.get(&current_state)
                && current_state != (0, 0, 0, 0, 0, 0)
            {
                let (_, _, v_x, v_y, tick_x, tick_y) = current_state;
                let (_, _, prev_v_x, prev_v_y, prev_tick_x, prev_tick_y) = *prev_state;

                // if speed has changed add it to the list
                // if the tick is greater or equal to the previous tick, it had to underflow
                // meaning we continued again at the previous speed
                if v_x != prev_v_x || tick_x >= prev_tick_x {
                    moves_x.push(prev_v_x);
                }
                if v_y != prev_v_y || tick_y >= prev_tick_y {
                    moves_y.push(prev_v_y);
                }

                current_state = *prev_state;
            }
            moves_x.reverse();
            moves_y.reverse();

            let elapsed = start.elapsed();
            eprintln!("Done {i} in {elapsed:?} with {time}/{max_t} steps");

            return Ok((moves_x, moves_y));
        }

        let elapsed = tick_x.min(tick_y) + 1;

        let new_time = time + elapsed as u16;
        if new_time > max_t {
            continue;
        }

        let x_changes: &[(i16, i8, u8)] = if let Some(new_tick_x) = tick_x.checked_sub(elapsed) {
            &[(x, v_x, new_tick_x)]
        } else {
            let new_x = x + v_x.signum() as i16;
            &[-1, 0, 1].map(|dv| {
                (
                    new_x,
                    apply_acc(v_x, dv),
                    apply_acc(v_x, dv).unsigned_abs().saturating_sub(1),
                )
            })
        };

        let y_changes: &[(i16, i8, u8)] = if let Some(new_tick_y) = tick_y.checked_sub(elapsed) {
            &[(y, v_y, new_tick_y)]
        } else {
            let new_y = y + v_y.signum() as i16;
            &[-1, 0, 1].map(|dv| {
                (
                    new_y,
                    apply_acc(v_y, dv),
                    apply_acc(v_y, dv).unsigned_abs().saturating_sub(1),
                )
            })
        };

        for ((new_x, new_v_x, new_tick_x), (new_y, new_v_y, new_tick_y)) in
            itertools::iproduct!(x_changes, y_changes)
        {
            let new_state = (*new_x, *new_y, *new_v_x, *new_v_y, *new_tick_x, *new_tick_y);
            let new_entry = grid.entry(new_state);

            if let Entry::Occupied(old_time) = &new_entry
                && new_time >= *old_time.get()
            {
                continue;
            }

            new_entry.insert_entry(new_time);

            let new_heuristic =
                new_time + (new_x - x_target).unsigned_abs() + (new_y - y_target).unsigned_abs();

            queue.push(QueueItem {
                time: new_time,
                state: new_state,
                prev_state: state,
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
