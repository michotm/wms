# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

# TODO: drop this model on next release.
# The feature has been moved to `rest_log`.
#
# It has been tried several times
# to drop the class altogether w/ its related records in this module
# but the ORM is uncapable do delete many records directly relate to the model
# (selection fields values, server actions for crons, etc.)
# and the upgrade will be always broken
# because the model is not in the registry anymore.
#
# Example of the error:
# [2021-02-01 08:44:52,103 1 INFO odoodb ]odoo.addons.base.models.ir_model:
#     Deleting 2617@ir.model.fields.selection
#         (shopfloor.selection__shopfloor_log__severity__severe)
# 2021-02-01 08:44:52,107 1 WARNING odoodb odoo.modules.loading:
#     Transient module states were reset
# 2021-02-01 08:44:52,110 1 ERROR odoodb odoo.modules.registry:
#     Failed to load registry
# Traceback (most recent call last):
#   File "/odoo/src/odoo/modules/registry.py", line 86, in new
#     odoo.modules.load_modules(registry._db, force_demo, status, update_module)
#   File "/odoo/src/odoo/modules/loading.py", line 472, in load_modules
#     env['ir.model.data']._process_end(processed_modules)
#   File "/odoo/src/odoo/addons/base/models/ir_model.py", line 2012, in _process_end
#     record.unlink()
#   File "/odoo/src/odoo/addons/base/models/ir_model.py", line 1206, in unlink
#     not self.env[selection.field_id.model]._abstract:
#   File "/odoo/src/odoo/api.py", line 463, in __getitem__
#     return self.registry[model_name]._browse(self, (), ())
#   File "/odoo/src/odoo/modules/registry.py", line 177, in __getitem__
#     return self.models[model_name]
# KeyError: 'shopfloor.log'


class ShopfloorLog(models.Model):
    _name = "shopfloor.log"
    _description = "Legacy model for tracking REST calls: replacedy by rest.log"
    _order = "id desc"

    DEFAULT_RETENTION = 30  # days
    EXCEPTION_SEVERITY_MAPPING = {
        "odoo.exceptions.UserError": "functional",
        "odoo.exceptions.ValidationError": "functional",
        # something broken somewhere
        "ValueError": "severe",
        "AttributeError": "severe",
        "UnboundLocalError": "severe",
    }

    request_url = fields.Char(readonly=True, string="Request URL")
    request_method = fields.Char(readonly=True)
    params = fields.Text(readonly=True)
    # TODO: make these fields serialized and use a computed field for displaying
    headers = fields.Text(readonly=True)
    result = fields.Text(readonly=True)
    error = fields.Text(readonly=True)
    exception_name = fields.Char(readonly=True, string="Exception")
    exception_message = fields.Text(readonly=True)
    state = fields.Selection(
        selection=[("success", "Success"), ("failed", "Failed")],
        readonly=True,
    )
    severity = fields.Selection(
        selection=[
            ("functional", "Functional"),
            ("warning", "Warning"),
            ("severe", "Severe"),
        ],
        compute="_compute_severity",
        store=True,
        # Grant specific override services' dispatch_exception override
        # or via UI: user can classify errors as preferred on demand
        # (maybe using mass_edit)
        readonly=False,
    )

    @api.depends("state", "exception_name", "error")
    def _compute_severity(self):
        for rec in self:
            rec.severity = rec.severity or rec._get_severity()

    def _get_severity(self):
        if not self.exception_name:
            return False
        mapping = self._get_exception_severity_mapping()
        return mapping.get(self.exception_name, "warning")

    def _get_exception_severity_mapping_param(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("shopfloor.log.severity.exception.mapping")
        )
        return param.strip() if param else ""

    @tools.ormcache("self._get_exception_severity_mapping_param()")
    def _get_exception_severity_mapping(self):
        mapping = self.EXCEPTION_SEVERITY_MAPPING.copy()
        param = self._get_exception_severity_mapping_param()
        if not param:
            return mapping
        # param should be in the form
        # `[module.dotted.path.]ExceptionName:severity,ExceptionName:severity`
        for rule in param.split(","):
            if not rule.strip():
                continue
            exc_name = severity = None
            try:
                exc_name, severity = [x.strip() for x in rule.split(":")]
                if not exc_name or not severity:
                    raise ValueError
            except ValueError:
                _logger.info(
                    "Could not convert System Parameter"
                    " 'shopfloor.log.severity.exception.mapping' to mapping."
                    " The following rule will be ignored: %s",
                    rule,
                )
            if exc_name and severity:
                mapping[exc_name] = severity
        return mapping

    def _logs_retention_days(self):
        retention = self.DEFAULT_RETENTION
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("shopfloor.log.retention.days")
        )
        if param:
            try:
                retention = int(param)
            except ValueError:
                _logger.exception(
                    "Could not convert System Parameter"
                    " 'shopfloor.log.retention.days' to integer,"
                    " reverting to the"
                    " default configuration."
                )
        return retention

    def logging_active(self):
        retention = self._logs_retention_days()
        return retention > 0

    def autovacuum(self):
        """Delete logs which have exceeded their retention duration

        Called from a cron.
        """
        deadline = datetime.now() - timedelta(days=self._logs_retention_days())
        logs = self.search([("create_date", "<=", deadline)])
        if logs:
            logs.unlink()
        return True
