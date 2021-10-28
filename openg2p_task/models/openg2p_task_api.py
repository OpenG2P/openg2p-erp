from odoo.http import Controller, route, request


# getTaskById
# getSubTaskForTaskId
# getTaskByProcess
# getTasksforUser
# getTasksforRole
# createTask with stateTransition commands - reassign, changeRole, suspend, close, unassign, approve, reject, changeProgram,bulkReassign, bulkunassign


class Openg2pTaskApi(Controller):
    @route("/tasks", type="json", auth="user", methods=["GET"])
    def all_tasks(self):
        try:
            task = request.env["openg2p.task"].search([])

            tasks_all = []
            for t in task:
                tasks_all.append(t.api_json())

            if len(task) > 0:
                return {
                    "status": 200,
                    "message": "Success",
                    "id": id,
                    "task_details": tasks_all,
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "error": "No tasks exists",
                }
        except BaseException as e:
            return {"status": 400, "error": str(e)}

    @route("/task/<int:id>", type="json", auth="user", methods=["GET"])
    def get_task_by_id(self, id):
        try:
            task = request.env["openg2p.task"].search([("id", "=", id)])

            if len(task) > 0:
                task = task[0]
                return {
                    "status": 200,
                    "message": "Success",
                    "id": id,
                    "task_details": task.api_json(),
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "error": f"Error ! No task by the id {id} exists",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/sub-task/<int:id>", type="json", auth="user", methods=["GET"])
    def get_sub_task_for_task_id(self, id):
        try:
            subtasks = request.env["openg2p.task.subtype"].search(
                [("task_type_id", "=", id)]
            )

            if len(subtasks) > 0:
                subtasks = list(map(lambda x: x.api_json(), subtasks))

                return {
                    "status": 200,
                    "message": "Success",
                    "task_id": id,
                    "sub_task": subtasks,
                }
            else:
                return {
                    "status": 404,
                    "id": id,
                    "error": f"Error ! No sub-task for task by the id {id} exists",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/process/<int:id>", type="json", auth="user", methods=["GET"])
    def get_tasks_by_process(self, id):
        tasks = request.env["openg2p.task"].search([("process_id", "=", id)])

        try:
            if len(tasks) > 0:
                tasks = list(map(lambda x: x.api_json(), tasks))
                return {
                    "status": 200,
                    "message": "Success",
                    "task_count": len(tasks),
                    "process": id,
                    "task details": tasks,
                }
            else:
                return {
                    "status": 404,
                    "process": id,
                    "error": f"Error ! No task by the process {id} exists",
                }
        except BaseException as e:
            return {"status": 400, "id": id, "error": str(e)}

    @route("/tasks/user/<int:id>", type="json", auth="user", methods=["GET"])
    def get_tasks_for_user(self, id):
        tasks = request.env["openg2p.task"].search([("assignee_id", "=", id)])
        try:
            if len(tasks) > 0:
                tasks = list(map(lambda x: x.api_json(), tasks))
                return {
                    "status": 200,
                    "message": "Success",
                    "user-id": id,
                    "task_details": tasks,
                }
            else:
                return {
                    "status": 404,
                    "user-id": id,
                    "error": f"Error ! No tasks for the user {id} exists",
                }
        except BaseException as e:
            return {"status": 400, "user-id": id, "error": str(e)}

    @route("/tasks/role/<int:id>", type="json", auth="user", methods=["GET"])
    def get_tasks_for_role(self, id):
        tasks = request.env["openg2p.task"].search([])
        role = request.env["openg2p.task.role"].search([("id", "=", id)])
        tasks_details = []

        try:
            if role:
                for task in tasks:
                    if task.type_id.id == role.task_type_id.id:
                        tasks_details.append(task.api_json())

                return {
                    "status": 200,
                    "message": "Success",
                    "role-id": id,
                    "task_details": tasks_details,
                }
            else:
                return {
                    "status": 404,
                    "role-id": id,
                    "error": f"Error ! No tasks for the role-id {id} exists",
                }
        except BaseException as e:
            return {"status": 400, "role-id": id, "error": str(e)}
