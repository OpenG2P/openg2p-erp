import json

from odoo import models, fields, api


class Openg2pProcess(models.Model):
    _name = "openg2p.process"
    _description = "Processes for OpenG2P Tasks"

    process_type = fields.Many2one(
        "openg2p.process.type",
        string="Process type",
    )

    curr_process_stage = fields.Many2one(
        comodel_name="openg2p.process.stage",
        string="Current process stage",
        readonly=True,
        store=True,
    )

    process_completed = fields.Boolean(
        string="Is process completed",
        readonly=True,
        store=True,
    )

    process_stage_count = fields.Integer(
        string="Process Stage Count",
        store=False,
        compute="_compute_fields",
    )
    curr_process_stage_index = fields.Integer(
        string="Current Process Stage Index",
        store=False,
        compute="_compute_fields",
    )
    # for storing technical details, JSONified dict for different stage details
    context = fields.Text(
        string="Context Details",
        readonly=True,
        store=True,
    )

    @api.onchange("process_type")
    def onchange_process_type(self):
        stages = self.env["openg2p.process.stage"].search(
            [("id", "in", self.process_type.stages.ids)]
        )
        if stages and len(stages) > 0:
            self.process_stage_count = len(stages)
            self.curr_process_stage = stages[0]
            self.curr_process_stage_index = 1
        return {
            "domain": {
                "curr_process_stage": [("id", "in", self.process_type.stages.ids)],
            }
        }

    def _compute_fields(self):
        for rec in self:
            rec.process_stage_count = len(rec.process_type.stages.ids)
            print(rec.process_type.stages.ids, rec.curr_process_stage.id)
            if rec.curr_process_stage.id:
                try:
                    rec.curr_process_stage_index = (
                        rec.process_type.stages.ids.index(rec.curr_process_stage.id) + 1
                    )
                except BaseException as e:
                    print(e)
            if not rec.context:
                rec.context = json.dumps({}, indent=2)

    def name_get(self):
        for rec in self:
            yield rec.id, f"{rec.process_type.name} ({rec.id})"

    def get_id_from_ext_id(self, ext_id):
        return self.env.ref(f"openg2p_task.{ext_id}").id

    def get_ext_id_from_id(self, model, id):
        res = self.env["ir.model.data"].search(
            ["&", ("model", "=", model), ("res_id", "=", id)]
        )
        if res and len(res) > 0:
            return res[0].name
        return None

    def _update_context(self, event_code, obj_ids):
        if obj_ids is None:
            return
        context = json.loads(self.context)
        if not isinstance(obj_ids, (list, tuple, bool)):
            obj_ids = [obj_ids]
        context[event_code] = json.dumps(obj_ids)
        self.context = json.dumps(context, indent=2)

    def _update_task_list(self, task_id):
        context = json.loads(self.context)
        tasks = json.loads(context["tasks"])
        tasks.append(task_id)
        context["tasks"] = json.dumps(tasks)
        self.context = json.dumps(context, indent=2)

    def update_curr_stage(self, event_code=None):
        if event_code:
            latest_event_id = self.get_id_from_ext_id(event_code)
            for idx, stage in enumerate(self.process_type.stages):
                if stage.task_subtype_id.id == latest_event_id:
                    self.curr_process_stage_index = idx + 1
                    self.curr_process_stage = self.process_type.stages[process_stage].id
        else:
            ext_ids = list(
                map(
                    lambda x: self.get_ext_id_from_id(
                        "openg2p.task.subtype", x.task_subtype_id.id
                    ),
                    self.process_type.stages,
                ),
            )
            context = json.loads(self.context)
            for idx, ext_id in enumerate(ext_ids):
                print("update_curr_stage-else", idx, ext_id)
                if ext_id not in context:
                    self.curr_process_stage_index = idx + 1
                    self.curr_process_stage = self.process_type.stages[idx + 1].id
                    break

    def handle_intermediate_task(self):
        context = json.loads(self.context)
        task_code = self.get_ext_id_from_id(
            "openg2p.task.subtype", self.curr_process_stage.task_subtype_id.id
        )
        print("handle_intermediate_task", task_code)
        if task_code == "task_subtype_regd_make_beneficiary":
            regd_ids = json.loads(context["task_subtype_regd_create"])
            bene_ids = []
            for regd_id in regd_ids:
                print("handle_intermediate_task", regd_id)
                regd = self.env["openg2p.registration"].search([("id", "=", regd_id)])
                if regd and len(regd) > 0:
                    bene_ids.append(regd.task_convert_registration_to_beneficiary())
            print("handle_intermediate_task", task_code, bene_ids)
            self._update_context(task_code, True)
            self._update_context("task_subtype_beneficiary_create", bene_ids)
        elif task_code == "task_subtype_beneficiary_enroll_programs":
            prog_ids = []
            self._update_context("task_subtype_beneficiary_enroll_programs", prog_ids)
        elif task_code == "task_subtype_beneficiary_create_disbursement_batch":
            context = json.loads(self.context)
            bene_ids = json.loads(context["task_subtype_beneficiary_create"])
            batch_ids = self.env[
                "openg2p.beneficiary.transaction.wizard"
            ].task_create_batch(bene_ids)
            self._update_context(
                "task_subtype_beneficiary_create_disbursement_batch", batch_ids
            )
        self.update_curr_stage()
        next_task = self.env["openg2p.task"].create(
            {
                "subtype_id": self.curr_process_stage.task_subtype_id.id,
                "process_id": self.id,
                "status_id": 2,
            }
        )
        self._update_task_list(next_task.id)

    def handle_tasks(self, events, process=None):
        print("handle_tasks", events, process)
        """
        :param events: list of tuples of event_code and obj_ids,
                        ex: [('event1', [1,2,3]),('event2', 45), ('event3', (1,5))]
        :param process: object of this class
        :return: None
        """
        # if process instance is passed
        if process is not None:
            assert isinstance(process, self.__class__)
            for event in events:
                event_code, obj_ids = event
                process._update_context(event_code, obj_ids)
            process.update_curr_stage(events[-1][0])
            return

        # find task that is done
        subtype_id = self.get_id_from_ext_id(events[0][0])
        task = self.env["openg2p.task"].search(
            ["&", ("subtype_id", "=", subtype_id), ("status_id", "=", 2)]
        )
        if task and len(task) > 0:
            task = task[0]
            # find process for the task
            process = self.env["openg2p.process"].search([("id", "=", task.process_id)])
            if process and len(process) > 0:
                process = process[0]
                assert isinstance(process, self.__class__)
                for event in events:
                    event_code, obj_ids = event
                    print("handle_tasks", event_code, obj_ids)
                    process._update_context(event_code, obj_ids)
                process.update_curr_stage(events[-1][0])
                process.handle_intermediate_task()
            # try:
            #     stages = self.env['openg2p.process.stage'].search([('id', 'in', process.process_type.stages.ids)])
            #     if process.curr_process_stage_index != len(stages):
            #         # while process.curr_process_stage.intermediate and process.curr_process_stage.automated:
            #         #     process.handle_intermediate_task()
            #         #     process.update_curr_stage()
            #         next_task = self.env['openg2p.task'].create({
            #             "subtype_id": process.curr_process_stage.task_subtype_id.id,
            #             "process_id": process.id,
            #             "status_id": 2,
            #         })
            #         process._update_task_list(next_task.id)
            #     else:
            #         process.process_completed = True
            task.status_id = 3
            # except BaseException as e:
            #     print(e)

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        task = self.env["openg2p.task"].create(
            {
                "subtype_id": res.curr_process_stage.task_subtype_id.id,
                "process_id": res.id,
                "status_id": 2,
            }
        )
        res.context = json.dumps(
            {
                "tasks": json.dumps([task.id]),
            },
            indent=2,
        )
        return res

    def write(self, vals):
        if not self.context and vals.get("context") is None:
            vals["context"] = json.dumps({}, indent=2)
        return super().write(vals)
