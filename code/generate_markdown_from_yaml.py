#!/usr/bin/env python3
import yaml, pathlib, jinja2

# charger YAML
y = yaml.safe_load(open("data/requests.yaml", encoding="utf-8"))

# templates (place-les dans /templates si tu veux)
TEMPLATES = {
    "index": "content/{{ service }}/index.md",
    "registre": "content/registre/{{ service }}.md"
}

# moteur Jinja
env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
for key, path_tpl in TEMPLATES.items():
    src = open(f"templates/{key}.md", encoding="utf-8").read()
    tpl = env.from_string(src)
    out = tpl.render(**y)
    out_path = pathlib.Path(path_tpl.replace("{{ service }}", y["service"]))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"✅ Généré: {out_path}")
