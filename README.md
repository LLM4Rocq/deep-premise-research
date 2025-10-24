# Deep Premise Research

Premise selection is a bottleneck in formal proving. General LLMs can solve many informal math problems but often fail to produce verifiable Lean/Rocq proofs. Recent agentic systems that add retrieval and specialized prover models vastly improve results on strong formal benchmarks, which motivates training a dedicated premise-selection policy rather than memorizing a fixed library snapshot.

This repository explores how to train large language models with reinforcement learning so they can select the right premises while navigating large Rocq and Lean 4 libraries. The project turns finished proofs into supervision signals: each proof step yields a goal plus the premises that were actually used. Those (goal, premises) pairs then become the reward signal for an RL policy that must discover the same dependencies by browsing the codebase.

## RL Training (Premise Selection)

**State.** Goal + hypotheses + module/load-path context + selected premises so far + a rolling summary of outputs from tools.
**Actions.** `add_premise(p)` to include one premise; `stop` to finalize the set.  
**Tools available to the policy.**
- `toc(library_or_module)`: access a Table of Contents to discover symbols and modules.  
- `read(path)`: read a simplified view of a source file.  
- `sandbox(cmd)`: run proof-assistant interactions for checks.  
- `sample_uses(premise, k=3)`: return up to 3 random proofs that use the premise, with their initial goals.

**Reward.** Number of correct premises / number of total premises.

**Optimization.** GRPO.

**Training data.** The pipeline extracts step-wise (goal, premises) pairs from ~150 curated Rocq libraries and is being extended to Lean 4. The resulting dataset provides hundreds of thousands of pairs (ongoing).

**Rollout.** The agent interleaves tool calls and premise proposals.

**Evaluation.**  
- Top-k precision/recall for premise prediction.  

## How It Works

1. **Docker orchestration** — Step 0 (`script/steps/step_0_docker.py`) builds per-library Docker images (or reuses them) starting from the base images in `base-image/`. Each image installs the packages listed in a YAML configuration.
2. **Source extraction** — Step 1 (`step_1_sources.py`) launches a container, resolves OPAM metadata, and exports every `.v` source file for the selected packages into `<output>_sources.jsonl`.
3. **Metadata mining** — Step 2 (`step_2_metadata.py`) feeds each source file to `TinyRocqParser` through `pet-server`, retrieves the table of contents, load path, and transitive `Require` dependencies, and stores them in `<output>_metadata.jsonl`.
4. **Proof element extraction** — Step 3 (`step_3_elements.py`) replays each proof, records every intermediate goal, and attaches the premises that were requested through `About`/`Locate`. The final dataset lives in `<output>_elements.jsonl`.
5. **Full orchestration** — `script/all_steps.py` runs all stages in sequence for every configuration file in `config/`.

For example, the proof below produces two pairs:

```coq
Lemma mulVr : {in unit, left_inverse 1 inv *%R}.
Proof.
  (goal_1) rewrite /inv => x Ux; case: pickP => [y | no_y]; last by case/pred0P: Ux.
  (goal_2) by case/andP => _; move/eqP.
Qed.
```

* `(goal_1, [pickP, pred0P])`
* `(goal_2, [andP, eqP])`

Those pairs are the supervision signal for the RL agent that must rediscover the same premises by probing the codebase.

## Repository Layout

```
base-image/          Base Dockerfiles for Coq/Rocq + coq-lsp
config/              Library descriptors (YAML) consumed by the pipeline
export/              Sample outputs: *_sources.jsonl, *_metadata.jsonl, *_elements.jsonl
script/              Step runners and utilities (all_steps + individual steps)
src/config/          Configuration loader (OpamConfig)
src/parser/          Docker client plus TinyRocqParser proof instrumentation
tests/               Early unit tests for parser components
```

## Prerequisites

- Docker.
- Python 3.10+ and `pip`.

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Build the base image (once per platform).**

   ```bash
   docker build -t theostos/rocq-lsp:9.0 base-image/rocq-lsp
   docker build -t theostos/coq-lsp:8.20 base-image/coq-lsp
   ```

2. **Create a virtual environment and install dependencies.**

3. **Run the full pipeline.**

   ```bash
   python script/all_steps.py --config-path config/
   ```

   The command iterates through every YAML file under `config/`. Use `--rebuild True` to force Docker rebuilds or change timeouts and ports with the provided flags.

### Running Individual Steps

Run a single step if you need to resume a partial extraction:

```bash
python script/steps/step_0_docker.py --config-path config/coq-mathcomp.yaml
python script/steps/step_1_sources.py --config-path config/coq-mathcomp.yaml --new-config-path tmp.yaml
python script/steps/step_2_metadata.py --config-path config/coq-mathcomp.yaml --toc-timeout 600
python script/steps/step_3_elements.py --config-path config/coq-mathcomp.yaml --extract-timeout 180
```

Each step is idempotent: progress is tracked in the JSONL outputs, so reruns skip already processed proofs.

## Configuration Files

Every YAML file in `config/` follows this schema:

```yaml
name: theostos/coq-mathcomp      # Docker image name
output: export/output/coq-mathcomp
tag: '9.0'                       # Docker image tag
packages:                        # OPAM packages to install inside the image
  - coq-mathcomp-algebra
base_image: theostos/rocq-lsp:9.0
opam_env_path: /home/rocq/.opam/4.14.2+flambda
user: rocq
info_path: {}                    # Optional overrides when opam show lacks logpath
```

Adjust `packages` and `info_path` to target additional libraries. The `output` prefix controls where the JSONL files is written.

## Data Artifacts

- `<output>_sources.jsonl`: one entry per source file with the raw text and OPAM metadata.
- `<output>_metadata.jsonl`: adds the table of contents, dependencies, and load paths for each file.
- `<output>_elements.jsonl`: the main supervision dataset; every entry keeps the library info, the theorem statement, and the step-by-step proof states together with the premises inferred for that step.

## Working With The Data

- The `steps` array in `_elements` mirrors the tactic script. Each element lists the goal state before/after the tactic and the dependencies found through `About`/`Locate`.
- Combine consecutive steps into RL trajectories: the environment state is the goal plus available premises, while the action is the predicted set of premises.
- Use the `_metadata` load path entries to reconstruct the module environment when sampling from the dataset.

## Testing and Development

- Lightweight unit tests live under `tests/`. Run them with `python -m pytest` once you add new parsing logic.

## Roadmap

- Extend the dataset to Lean 4.
- Connect the dataset to RL framework.
- Training and Evaluation.
- IDE integration.
