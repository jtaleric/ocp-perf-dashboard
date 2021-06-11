from fastapi import APIRouter

import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
from app.models.airflow import Dag, DagRun
import semver
from app.core import airflow_transform
from app.services.airflow import AirflowService

router = APIRouter()
airflow_service = AirflowService()


@router.post('/api/airflow')
@router.get('/api/airflow')
def airflow():
    path = "api/v1/dags"
    response = airflow_service.get(path)
    parsed_dags = [
        {**dag, **parse_id(dag['dag_id']), **get_release_stream(dag['tags'])}
        for dag in response['dags']]
    dags = [Dag(**dag) for dag in parsed_dags]
    for dag in dags:
        dag.runs = get_runs(dag.dag_id)

    dags = [dag.dict() for dag in dags]
    return airflow_transform.build_airflow_dataframe(dags)


def parse_id(dag_id: str):
    return dict(zip(('version', 'platform', 'profile'), dag_id.split('_')))


def get_release_stream(tags: list):
    for tag in tags:
        if "-stable" in tag['name'] or semver.VersionInfo.isvalid(tag['name']):
            return {"release_stream": tag['name']}


def get_runs(dag_id: str):
    path = (
        f"api/v1/dags/{dag_id}"
        f"/dagRuns?limit=10&execution_date_gte=2021-04-18T15%3A40%3A39")
    response = airflow_service.get(path)
    return [DagRun(**run).dict() for run in response['dag_runs']]

# import trio
#
#
# async def get_tasks(tasks):
#
#     session = airflow_service.asks_client()
#     results = []
#
#     async def grabber(s, upstream_job, upstream_job_build, build_tag):
#         # f"{airflow_service.url}/api/v1"
#         # f"/dags/{task['upstream_job']}"
#         # f"/dagRuns/{task['upstream_job_build']}"
#         # f"/tasksInstances/{task['build_tag']}"
#         t = await s.get((
#             f"{airflow_service.url}/api/v1"
#             f"/dags/{upstream_job}"
#             f"/dagRuns/{upstream_job_build}"
#             f"/tasksInstances/{build_tag}"
#         ))
#         results.append(
#             dict(
#                 pipeline_id=t['dag_id'], job_id=upstream_job_build,
#                 task_id=build_tag, state=t['state']
#             )
#         )
#
#     async def main(task_list):
#         async with trio.open_nursery() as n:
#             for task in task_list:
#                 n.start_soon(
#                     grabber,
#                     session,
#                     task['upstream_job'],
#                     task['upstream_job_build'],
#                     task['build_tag']
#                 )
#     trio.run(main, tasks)
#
#     pprint(results)



