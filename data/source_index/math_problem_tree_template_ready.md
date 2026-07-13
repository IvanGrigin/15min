# Template-Ready Math Problem Tree

This file is a production-oriented tree for future JSON templates. It is based on:

- `docs/math_problem_tree_100_themes.md`
- `docs/math_problem_tree_full_coverage.md`
- `docs/template_coverage_report.md`
- `data/templates/problem_templates.json`

It does not replace the source corpus or the full coverage files. It translates the 100-theme taxonomy into generator-ready leaves that can become records in `data/templates/problem_templates.json`.

## Template Rules

- Every leaf must become one or more static JSON templates with `template_text`, `placeholders`, `constraints`, `number_strategy`, `answer_formula` or a named validator.
- A generated task should require at least three meaningful solution actions, unless the leaf is intentionally marked as a drill.
- Characters and locations are optional story wrappers. The mathematical model must work without changing the template text.
- Difficulty is stored on template records as `difficulty` and `supported_difficulties`, not as nested tree branches.
- Each numeric placeholder must have integer constraints and a validator for positivity, integrality, uniqueness, and answer correctness.
- Prefer compound templates over one-step templates. For example, use "find total, remove used amount, compare remaining parts" instead of "add two numbers".

## Difficulty and Action Model

| Band | Generator target | Minimum solution actions |
|---|---|---:|
| D1 | warmup_drill | 2 |
| D2 | routine_multistep | 3 |
| D3 | model_selection | 4 |
| D4 | olympiad_insight | 5 |
| D5 | proof_or_construction | 6 |

## Current Implemented Bridges

| Existing module | Current JSON template IDs | Better tree leaves |
|---|---|---|
| `joint_work` | `joint_work_olympiads_001`, `joint_work_books_002` | `B07`, `J01` |
| `ages` | `ages_total_001` | `B02` |
| `heads_and_legs` | `heads_and_legs_001` | `B05` |
| `ratios` | `ratio_berries_001` | `B03` |
| `round_robin` | `round_robin_001` | `F06` |
| `paint_cube` | `paint_cube_001` | `H08`, `G06` |
| `money` | `equal_payment_001` | `B04`, `B10` |
| `movement` | `movement_together_001` | `J01`, `J02` |

## A. Arithmetic and Expressions

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| A01 | `expression_value` | Evaluate a long expression after grouping repeated factors and exact divisions. | `a,b,c,d,k1,k2,divisor,offset` | arithmetic expression evaluator with exact division checks | 3 |
| A02 | `nested_expression_chain` | Reverse or evaluate a nested expression with 4-6 operations and one hidden intermediate. | `start,step_1,step_2,step_3,divisor,target` | reverse chain validator; all intermediate values integer | 4 |
| A03 | `factor_shortcut` | Compare or evaluate two products after extracting a common factor and simplifying a difference. | `n,delta_1,delta_2,common,scale` | symbolic difference formula | 4 |
| A04 | `large_product_comparison` | Compare two large structured products without full multiplication, then find the difference. | `a,b,c,shift_1,shift_2,common_factor` | transformed product difference | 4 |
| A05 | `long_division_exact` | Large exact division followed by a second condition on quotient digits or remainder-free grouping. | `quotient,divisor,block_size,check_digit` | `N = quotient * divisor`; optional digit validator | 3 |
| A06 | `leading_digit_classifier` | Choose all expressions whose result starts with a given digit from a generated list. | `expressions,target_digit,min_true,max_true` | exact evaluator plus first-digit classifier | 5 |
| A07 | `integer_inequality_bound` | Solve an inequality where the bound is a nested exact expression. | `a,b,c,d,e,f,coef,shift` | floor bound and interval validator | 4 |
| A08 | `reverse_truncation_chain` | Recover an integer after multiply-and-delete-last-digit operations. | `initial,mult_1,mult_2,final,digit_1,digit_2` | reverse interval search with uniqueness | 5 |

## B. Algebraic Modelling

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| B01 | `linear_equation_chain` | One-variable equation built from nested operations and exact division. | `x,a,b,c,d,e,target` | generated from hidden `x`; solve by reverse operations | 4 |
| B02 | `ages` | Total age changes twice, then one participant leaves or joins before asking for count. | `current_total,years_later,future_total,extra_people,extra_years` | linear total-age formula | 3 |
| B03 | `ratios` | Split a total after one transfer changes the ratio, asking for the original amount. | `ratio_a,ratio_b,total,transfer,part_name` | two-step ratio equation | 4 |
| B04 | `money` | Shared payment with loans, partial payments, and a final equalization transfer. | `total,loan,paid_1,paid_2,people_count` | net contribution balance | 4 |
| B05 | `heads_and_legs` | Heads-and-legs with two animal types plus a later removed subgroup. | `heads,legs,type_a_legs,type_b_legs,removed` | two-variable linear system | 4 |
| B06 | `price_system` | Mixed purchases with two receipts and one unknown item count or price. | `price_a,price_b,count_a_1,count_b_1,total_1,total_2` | linear system with integer solution | 4 |
| B07 | `joint_work` | Two or three workers with different rates, one works only part of the time. | `rate_1_time,rate_1_amount,rate_2_time,rate_2_amount,duration,delay` | rate sum with partial interval | 4 |
| B08 | `percent_concentration` | Mixture or percent change with removal/addition and conserved substance. | `volume_1,percent_1,volume_2,percent_2,removed` | conserved amount equation | 5 |
| B09 | `direct_proportion` | Scale cost/mass/length through two proportional steps and a remainder. | `unit_a,unit_b,total_cost,known_amount,extra_amount` | proportional ratio with integer constraints | 3 |
| B10 | `transfer_difference` | Several transfers change the difference between two amounts; recover original amounts. | `sum_total,initial_diff,transfer_1,transfer_2,target_diff` | invariant sum and changing difference | 4 |

## C. Digits and Decimal Notation

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| C01 | `interval_parity_count` | Count even/odd numbers in a shifted interval after excluding multiples of another number. | `left,right,parity,excluded_mod,excluded_residue` | interval count minus filtered count | 4 |
| C02 | `contains_digit_count` | Count numbers in a range containing a digit, with leading-zero restrictions. | `digits_count,target_digit,lower,upper` | complement counting validator | 4 |
| C03 | `avoid_digit_count` | Count numbers avoiding one digit and satisfying parity or divisibility. | `digits_count,banned_digit,modulus,residue` | digit DP or product rule with filter | 5 |
| C04 | `digit_frequency_block` | Count occurrences of a digit while writing consecutive numbers from `start` to `end`. | `start,end,target_digit` | positional frequency counter | 5 |
| C05 | `adjacent_digit_rules` | Count numbers where neighboring digits satisfy parity or inequality constraints. | `length,allowed_digits,rule_type` | finite-state DP | 5 |
| C06 | `first_last_digit_expression` | Determine first and last digits of a structured expression. | `a,b,c,d,operation_pattern` | modular arithmetic plus magnitude estimate | 4 |
| C07 | `digit_sum_construction` | Build or count long numbers with fixed digit sum and extra first/last digit condition. | `length,digit_sum,first_rule,last_rule` | bounded composition with digit caps | 5 |
| C08 | `positional_digit_inequality` | Count numbers whose hundreds/tens/ones digits satisfy several inequalities. | `length,relations,allowed_zero_positions` | constrained enumeration validator | 4 |
| C09 | `multiset_digit_numbers` | Count numbers from a multiset of digits with a divisibility condition. | `digit_multiset,length,modulus` | permutations with repeated digits and filter | 5 |
| C10 | `cryptarithm_missing_digits` | Restore missing digits in an arithmetic column with carries. | `operation,mask,base_digits` | carry-based uniqueness search | 5 |
| C11 | `same_suffix_numbers` | Several numbers share a suffix; use sum/difference/divisibility to recover suffix. | `suffix_length,leading_digits,total,difference` | base-10 decomposition | 4 |
| C12 | `consecutive_digit_block` | Recover the first or last number in a consecutive block from total written digits. | `start,end,count_digits,block_length` | digit-length block equation | 4 |

## D. Number Theory

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| D01 | `multiples_interval` | Count multiples in an interval after removing multiples of a second number. | `left,right,mod_a,mod_b` | inclusion-exclusion with floor divisions | 4 |
| D02 | `divisibility_missing_residue` | Fill missing digit(s) so a number is divisible by several moduli. | `number_mask,moduli,allowed_digits` | residue search with uniqueness | 4 |
| D03 | `factor_pair_min_sum` | Find factor pair with minimum sum under parity or interval restrictions. | `product,min_factor,max_factor,parity` | divisor search and optimization | 4 |
| D04 | `constrained_factorization` | Count or find factorizations with bounds and distinctness. | `product,factor_count,min_value,max_value` | recursive divisor enumeration | 5 |
| D05 | `prime_parameter` | Use primality constraints to recover one number from sum/product clues. | `sum_value,product_value,prime_bounds` | prime filter plus equation | 4 |
| D06 | `gcd_lcm_periods` | Two periodic events coincide; ask for first or number of coincidences in a range. | `period_1,period_2,start_offset,end_time` | lcm/gcd formula | 4 |
| D07 | `modular_cycle` | Find residue or last digit after repeated operation or power cycle. | `base,exponent,modulus,operation` | cycle detection | 4 |
| D08 | `trailing_zeros` | Count trailing zeros after multiplying selected terms from an interval. | `start,end,step,extra_factor` | min(count_2,count_5) | 4 |
| D09 | `parity_divisibility_construction` | Decide whether a construction is possible under parity/divisibility constraints. | `count,total,parity_rule,divisor` | invariant or constructive validator | 5 |

## E. Sequences and Patterns

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| E01 | `arithmetic_progression_sum` | Recover term count or common difference from a partial sum and endpoint clue. | `first,last,difference,count,sum_value` | AP formulas with integer check | 4 |
| E02 | `alternating_block_sum` | Evaluate a long alternating or block sum using cancellation. | `block_size,block_count,start,step,sign_pattern` | grouped sum formula | 4 |
| E03 | `pattern_recognition` | Find the next terms after identifying a two-layer pattern. | `seed_terms,rule_params,target_index` | generated recurrence validator | 4 |
| E04 | `fibonacci_type` | Sequence where each term depends on previous two; recover missing term or index. | `term_1,term_2,index,target` | recurrence forward/backward | 5 |
| E05 | `iterative_number_process` | Repeated operation until threshold or target, asking first time reached. | `start,operations,threshold,max_steps` | simulation with invariant check | 5 |
| E06 | `recursive_total_growth` | Accumulating totals where each day depends on previous total and new addition. | `initial,days,multiplier,addition,query_day` | recurrence formula or simulation | 4 |

## F. Combinatorics

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| F01 | `permutations_distinct` | Count arrangements with one position restriction and one adjacency restriction. | `items_count,fixed_positions,forbidden_neighbors` | permutation count with inclusion-exclusion | 5 |
| F02 | `permutations_repeated` | Count words from repeated letters with first/last restrictions. | `letter_counts,first_rule,last_rule` | multinomial with filters | 5 |
| F03 | `bounded_words` | Count words of length range over alphabet with at least one required symbol. | `alphabet_size,min_len,max_len,required_symbol_count` | total minus complement | 4 |
| F04 | `unknown_alphabet_order` | Recover lexicographic order from several sorted words, then rank a new word. | `words,alphabet_symbols,target_word` | topological sort and rank | 6 |
| F05 | `team_selection` | Select a team with role minimums and exclusions. | `group_sizes,team_size,min_by_group,forbidden_pairs` | combinations with cases | 5 |
| F06 | `round_robin` | Tournament with missing games or groups, asking total played/remaining games. | `players,groups,played_per_player,missing_games` | pair count minus known count | 4 |
| F07 | `single_elimination` | Knockout tournament with byes and extra consolation matches. | `players,bye_count,extra_matches` | elimination invariant | 4 |
| F08 | `lattice_paths` | Count monotone paths through a required point while avoiding one blocked point. | `width,height,required_point,blocked_point` | product of binomial counts minus blocked | 5 |
| F09 | `weighted_grid_paths` | Count grid paths with target weight sum. | `grid_weights,start,end,target_sum` | DP over paths and weights | 6 |
| F10 | `chess_placements` | Place nonattacking pieces with row/column restrictions. | `board_size,piece_count,blocked_cells` | backtracking or formula | 6 |
| F11 | `pigeonhole_guarantee` | Minimum draws to guarantee several properties at once. | `color_counts,required_by_color,guarantee_target` | worst-case complement | 4 |

## G. Plane Geometry and Measurement

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| G01 | `square_area_perimeter` | Square changes side, then compare area and perimeter changes. | `side,side_delta,scale` | area/perimeter formulas | 3 |
| G02 | `rectangle_area_perimeter` | Rectangle with fixed perimeter and changed side relation; recover dimensions. | `perimeter,ratio_a,ratio_b,delta` | linear equation for sides | 4 |
| G03 | `composite_rectangles` | Figure from equal squares with missing part; find area/perimeter. | `cell_size,rows,cols,removed_cells` | cell count plus boundary count | 5 |
| G04 | `perimeter_after_cut` | Cutting a rectangle into parts; compare total perimeter before and after. | `width,height,cut_lengths,cut_count` | added boundary formula | 4 |
| G05 | `integer_rectangle_constraints` | Find integer rectangle sides from area/perimeter relation and bounds. | `area,perimeter,min_side,max_side` | divisor search | 5 |
| G06 | `area_scaling` | Scale a figure twice and compare areas or material use. | `base_area,scale_1,scale_2,removed_fraction` | square scaling with subtraction | 4 |
| G07 | `unit_density_conversion` | Convert units and compute density over area or volume with leftover material. | `density,area,unit_scale,loss_percent` | unit conversion and multiplication | 4 |
| G08 | `grid_square_count` | Count all squares in a grid after removing a row/column or blocked cell. | `rows,cols,removed_lines` | summation over square sizes | 5 |
| G09 | `collinear_segments` | Ordered points with several segment sums/differences; recover a distance. | `segment_1,segment_2,total,difference` | linear system on segments | 4 |
| G10 | `repeated_line_distances` | Sum distances between consecutive marked points with repeating gaps. | `gap_pattern,repetitions,start,end` | pattern sum | 4 |
| G11 | `liquid_layer_depth` | Pour volume into rectangular tray after unit conversion and spill/loss. | `volume,base_length,base_width,loss,unit_scale` | volume / area | 4 |
| G12 | `rectangle_composition_ratio` | Compose rectangles with side ratio, then infer missing dimension or count. | `ratio_a,ratio_b,pieces,total_area,total_perimeter` | ratio equations | 5 |

## H. Grid and Solid Geometry

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| H01 | `grid_partitions` | Count internal partitions in an `m x n` cell rectangle after removing some walls. | `rows,cols,removed_vertical,removed_horizontal` | grid edge count | 4 |
| H02 | `grid_partitions_holes` | Partition a grid figure with holes; find added or remaining edges. | `rows,cols,hole_cells,cut_edges` | boundary and adjacency count | 5 |
| H03 | `polyomino_boundary` | Cell-grid letters or shapes; compute perimeter after attaching copies. | `shape_cells,copies,shared_edges` | `4*cells - 2*adjacencies` | 5 |
| H04 | `cutting_boards` | Minimum cuts or time to cut boards into equal pieces with stacking allowed. | `boards,pieces_per_board,stack_limit,cut_time` | cutting schedule validator | 5 |
| H05 | `cuboid_blocks` | Cut cuboid into unit blocks, then remove a layer or count internal blocks. | `x,y,z,removed_layer` | product and layer formulas | 4 |
| H06 | `cuboid_cutting_compare` | Compare two cutting schemes by number of cuts or produced blocks. | `x1,y1,z1,x2,y2,z2,stacking_rule` | scheme evaluator | 5 |
| H07 | `painted_cube_faces` | Count small cubes with exactly k painted faces after repainting or removing layer. | `side,k,removed_layer` | cube-face classification | 5 |
| H08 | `paint_cube` | Paint a scaled cuboid/cube, then compare paint after one face is not painted. | `base_side,base_paint,scale,unpainted_faces` | surface area scaling | 4 |
| H09 | `cube_face_labels` | Determine labels on hidden or visible faces of small cubes cut from a labeled cube. | `side,visible_faces,label_rules` | face-position classification | 6 |

## I. Time, Calendars, and Clocks

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| I01 | `weekday_after_days` | Find weekday after adding days and excluding weekends or holidays. | `start_weekday,days,excluded_days` | modulo 7 plus filter | 3 |
| I02 | `weekday_counts_month` | Count how many times selected weekdays occur in a month. | `days_in_month,start_weekday,target_weekdays` | quotient and remainder by 7 | 4 |
| I03 | `nth_weekday_month` | Find last or nth weekday under date bounds. | `days_in_month,start_weekday,n,target_weekday` | calendar index formula | 4 |
| I04 | `time_zone_direct` | Convert local time across zones after flight duration and date boundary. | `depart_time,utc_from,utc_to,duration` | minute arithmetic mod 24h | 4 |
| I05 | `multi_leg_timezones` | Trip with connection, time zones, and waiting time; recover arrival time. | `leg_1,wait,leg_2,utc_a,utc_b,utc_c` | chained time conversion | 5 |
| I06 | `turnaround_local_time` | Round trip with same route time and local timestamps; recover flight duration. | `depart_local,arrival_local,utc_a,utc_b,turnaround_wait` | equation in minutes | 5 |
| I07 | `clock_drift` | Clock gains/loses time over interval; find true time or displayed time. | `drift_per_hour,elapsed_time,shown_time` | proportional drift equation | 4 |
| I08 | `digital_clock_display` | Count times when display satisfies digit property, with possible broken segment. | `start_time,end_time,digit_rule,segment_rule` | minute enumeration validator | 5 |

## J. Motion and Rates

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| J01 | `movement` | Basic distance-speed-time with two stages and a stop or delay. | `speed_1,time_1,speed_2,time_2,delay` | piecewise distance sum | 4 |
| J02 | `opposite_motion` | Two movers start apart, one delayed; find meeting time or distance. | `distance,speed_1,speed_2,delay` | relative speed equation | 4 |
| J03 | `catch_up_motion` | Catch-up with head start and possible speed change. | `head_start,speed_slow,speed_fast,change_time` | relative distance equation | 4 |
| J04 | `three_movers` | Three movers with pairwise meeting times; recover hidden distance or speed. | `speed_1,speed_2,speed_3,time_a,time_b` | system of motion equations | 5 |
| J05 | `turnaround_motion` | Out-and-back movement with turnaround and different speeds. | `speed_out,speed_back,total_time,wait_time` | distance equality equation | 5 |
| J06 | `average_speed_piecewise` | Average speed over several segments with different speeds and distances. | `distance_1,distance_2,speed_1,speed_2` | total distance / total time | 4 |
| J07 | `circular_motion` | Circular track, laps, meetings, and overtakings. | `track_length,speed_1,speed_2,laps,target_meet` | modular relative motion | 5 |

## K. Logic, Invariants, and Algorithms

| ID | Generator module | Production template family | Required variables | Answer model | Min actions |
|---|---|---|---|---|---:|
| K01 | `truth_liars` | Role deduction with 3-5 statements and exactly one consistent assignment. | `characters,roles,statements,true_role_count` | exhaustive assignment validator | 5 |
| K02 | `one_wrong_calculation` | Several people multiply same hidden number; exactly one result is wrong. | `hidden,multipliers,reported_results,wrong_index` | divisibility and uniqueness check | 5 |
| K03 | `elevator_reachability` | Elevator with +a/-b buttons, building bounds, and two target trips. | `floors,up_step,down_step,start_1,end_1,start_2,end_2` | BFS plus gcd precheck | 5 |
| K04 | `parity_invariant_grid` | Fill or color a board under parity conditions on rows, columns, or neighbors. | `rows,cols,parity_rules,color_count` | parity invariant or construction | 6 |
| K05 | `neighbor_difference_invariant` | Neighboring quantities differ by fixed value; decide if total is possible and construct example. | `n,d,total,min_value` | modular invariant plus construction | 6 |
| K06 | `guaranteed_draw_composition` | Infer hidden composition from guarantees about arbitrary samples. | `types,sample_sizes,guarantee_types,total` | complement bounds and uniqueness | 6 |
| K07 | `ordered_clue_deduction` | Recover labels, dates, or positions from inequalities and calendar/order clues. | `objects,positions,clues,calendar_range` | exhaustive uniqueness validator | 5 |
| K08 | `state_reachability` | Transform state with operations; ask possibility and minimum steps. | `start,target,operations,bounds` | BFS or invariant validator | 6 |

## Implementation Priority

| Priority | Leaves | Why |
|---|---|---|
| P1 | `B02`, `B03`, `B04`, `B05`, `B07`, `F06`, `H08`, `J01` | Already close to `problem_templates.json`; can be improved by adding partial stages and stricter strategies. |
| P2 | `A03`, `A04`, `B06`, `J02`, `J03`, `G02`, `G06`, `I04` | Natural next templates: formula-driven, integer-safe, good for worksheets. |
| P3 | `C02`, `D01`, `D06`, `F11`, `G08`, `H07`, `I02`, `K02` | Need validators but still deterministic and practical. |
| P4 | `C10`, `F04`, `F09`, `F10`, `K01`, `K03`, `K04`, `K08` | Need search/DP validators before adding many JSON records. |

## Example JSON Template Shape

```json
{
  "template_id": "opposite_motion_delay_001",
  "domain": "motion",
  "module": "opposite_motion",
  "topic": "relative_speed_with_delay",
  "problem_type": "linear_motion",
  "difficulty": 5,
  "supported_difficulties": [3, 4, 5, 6, 7],
  "title": "Встречное движение с задержкой",
  "template_text": "{character_1} и {character_2} находятся на расстоянии {distance} км. {character_1} выходит сразу со скоростью {speed_1} км/ч, а {character_2} выходит через {delay} {hour_word_1} навстречу со скоростью {speed_2} км/ч. Через сколько часов после выхода {character_1} они встретятся?",
  "placeholders": {
    "characters": ["character_1", "character_2"],
    "locations": [],
    "numbers": ["distance", "speed_1", "speed_2", "delay"]
  },
  "constraints": {
    "distance": {"type": "integer", "min": 10, "max": 500},
    "speed_1": {"type": "integer", "min": 2, "max": 80},
    "speed_2": {"type": "integer", "min": 2, "max": 80},
    "delay": {"type": "integer", "min": 1, "max": 5}
  },
  "number_strategy": "opposite_motion_delay",
  "answer_formula": "delay + (distance - speed_1 * delay) / (speed_1 + speed_2)",
  "answer_type": "number",
  "integer_answer_required": true,
  "derived_words": {
    "hour_word_1": {"number": "delay", "forms": ["час", "часа", "часов"]}
  }
}
```

