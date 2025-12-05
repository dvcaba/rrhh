from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

from smart_filtering.config import load_config, resolve_path
from smart_filtering.generator.run_generation import create_cvs_as_docx
from smart_filtering.generator.run_jd_generation import create_jds_as_docx, JD_ROLES
from smart_filtering.parser.docx_parser import parse_docx_cv, parse_docx_jd
from smart_filtering.ranker.score import calculate_score


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smart-filtering",
        description="CLI para generación de CVs y JDs en formato DOCX",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-cv
    cv_parser = subparsers.add_parser("generate-cv", help="Genera CVs DOCX de ejemplo")
    cv_parser.add_argument("--n", type=int, default=15, help="Número de CVs a generar")
    cv_parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Directorio de salida (por defecto usa config.data.cvs_dir)",
    )
    cv_parser.add_argument("--seed", type=int, default=None, help="Seed para reproducibilidad")

    # generate-jd
    jd_parser = subparsers.add_parser("generate-jd", help="Genera JDs DOCX de ejemplo")
    jd_parser.add_argument(
        "--roles",
        type=str,
        default=",".join(JD_ROLES),
        help=f"Roles separados por coma (default: {', '.join(JD_ROLES)})",
    )
    jd_parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Directorio de salida (por defecto usa config.data.jds_dir)",
    )
    jd_parser.add_argument("--seed", type=int, default=None, help="Seed para reproducibilidad")

    # rank
    rank_parser = subparsers.add_parser(
        "rank", help="Rankea CVs contra un JD y exporta CSV con scores"
    )
    rank_parser.add_argument(
        "--jd-role",
        type=str,
        default=None,
        help="Rol del JD a usar (si no se indica, toma el primer JD disponible)",
    )
    rank_parser.add_argument(
        "--cvs-dir",
        type=str,
        default=None,
        help="Directorio de CVs DOCX (default: config.data.cvs_dir)",
    )
    rank_parser.add_argument(
        "--jds-dir",
        type=str,
        default=None,
        help="Directorio de JDs DOCX (default: config.data.jds_dir)",
    )
    rank_parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Ruta del CSV de salida (default: data/outputs/shortlist.csv)",
    )
    rank_parser.add_argument(
        "--skill-weight-strength",
        type=float,
        default=None,
        help="Peso adicional de skill alignment (default: config.ranking.default_skill_weight_strength)",
    )

    return parser


def _resolve_output_dir(out_arg: str | None, config_key: str, project_root: Path) -> Path:
    cfg = load_config()
    data_cfg = cfg.get("data", {})
    default_dir = data_cfg.get(config_key)
    target = out_arg or default_dir
    if not target:
        raise ValueError(f"No se pudo resolver la ruta para {config_key}. Revise config/default.yaml.")
    return resolve_path(target, project_root=project_root)


def _load_jds(jd_dir: Path) -> List[Dict[str, Any]]:
    jds: List[Dict[str, Any]] = []
    for path in sorted(jd_dir.glob("*.docx")):
        if path.name.startswith("~"):  # skip temp
            continue
        jd = parse_docx_jd(str(path))
        if jd and jd.get("id"):
            jds.append(jd)
    return jds


def _load_cvs(cv_dir: Path) -> List[Dict[str, Any]]:
    cvs: List[Dict[str, Any]] = []
    for path in sorted(cv_dir.glob("*.docx")):
        if path.name.startswith("~"):
            continue
        cv = parse_docx_cv(str(path))
        if cv and cv.get("id"):
            cvs.append(cv)
    return cvs


def _rank(jds: List[Dict[str, Any]], cvs: List[Dict[str, Any]], jd_role: str | None, skill_weight_strength: float) -> List[Dict[str, Any]]:
    if not jds:
        raise ValueError("No se encontraron JDs para rankear.")
    if not cvs:
        raise ValueError("No se encontraron CVs para rankear.")

    jd_map = {jd["role"]: jd for jd in jds if jd.get("role")}
    jd = None
    if jd_role:
        jd = jd_map.get(jd_role)
        if jd is None:
            raise ValueError(f"No se encontró JD con rol '{jd_role}'. Roles disponibles: {list(jd_map.keys())}")
    else:
        jd = jds[0]

    scored = []
    for cv in cvs:
        score_result = calculate_score(cv, jd, skill_weights=None, skill_weight_strength=skill_weight_strength)
        scored.append(
            {
                "cv_id": cv["id"],
                "name": cv["name"],
                "score": score_result["score"],
                "reason": score_result.get("reason", ""),
                "experience_years_total": cv.get("experience_years_total", 0),
                "location_city": cv.get("location", {}).get("city", ""),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def _write_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    project_root = Path(__file__).resolve().parents[2]

    seed = getattr(args, "seed", None)
    if seed is not None:
        random.seed(seed)

    if args.command == "generate-cv":
        out_dir = _resolve_output_dir(args.out, "cvs_dir", project_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        create_cvs_as_docx(str(out_dir), num_cvs=args.n)
        return 0

    if args.command == "generate-jd":
        out_dir = _resolve_output_dir(args.out, "jds_dir", project_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        roles = [r.strip() for r in args.roles.split(",") if r.strip()]
        create_jds_as_docx(str(out_dir), roles=roles)
        return 0

    if args.command == "rank":
        cfg = load_config()
        data_cfg = cfg.get("data", {})
        ranking_cfg = cfg.get("ranking", {})
        cvs_dir = resolve_path(args.cvs_dir or data_cfg.get("cvs_dir", "data/raw/cvs"), project_root=project_root)
        jds_dir = resolve_path(args.jds_dir or data_cfg.get("jds_dir", "data/raw/jds"), project_root=project_root)

        outputs_dir = data_cfg.get("outputs_dir", "data/outputs")
        default_out = Path(outputs_dir) / "shortlist.csv"
        out_path = resolve_path(args.out or default_out, project_root=project_root)

        skill_weight_strength = args.skill_weight_strength
        if skill_weight_strength is None:
            skill_weight_strength = float(ranking_cfg.get("default_skill_weight_strength", 0.25))

        jds = _load_jds(jds_dir)
        cvs = _load_cvs(cvs_dir)
        rows = _rank(jds, cvs, args.jd_role, skill_weight_strength)
        _write_csv(rows, out_path)
        print(f"Shortlist exportada a {out_path}")
        return 0

    parser.error("Comando no soportado")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
