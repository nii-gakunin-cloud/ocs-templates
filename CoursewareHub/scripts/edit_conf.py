from pathlib import Path

from IPython.core.display import HTML
from jupyter_server.serverapp import list_running_servers


def generate_edit_link(conf: Path) -> HTML:
    servers = list(list_running_servers())
    if len(servers) > 0:
        nb_conf = servers[0]
        p = Path(nb_conf["base_url"]) / "edit" / conf.absolute().relative_to(nb_conf["root_dir"])
    else:
        p = conf.absolute()
    return HTML(f'<a href={p} target="_blank">{p.name}</a>')
