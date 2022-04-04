from urllib.parse import parse_qs
from app.models import Project


def get_q(query, param):
    query_dict = parse_qs(query[1:])
    return query_dict[param][0]


def get_breadcrumbs(query):
    project_id = get_q(query, 'project')
    project = Project.query.get(project_id)
    items = [
        {'label': 'Projects', 'href': '/projects', 'external_link': True},
        {'label': project.name, 'href': '/projects/{id}/overview'.format(id=project_id), 'external_link': True},
        {'label': 'Visualize', 'href': '/visualize/project/{id}'.format(id=project_id), 'external_link': True},
    ]
    return items
