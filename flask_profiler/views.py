from dataclasses import dataclass

from flask import Request, Response, jsonify

from flask_profiler.controllers.get_timeseries_controller import GetTimeseriesController
from flask_profiler.presenters.get_timeseries_presenter import GetTimeseriesPresenter
from flask_profiler.use_cases.get_timeseries_use_case import GetTimeseriesUseCase


@dataclass
class GetRequestsTimeseriesView:
    use_case: GetTimeseriesUseCase
    controller: GetTimeseriesController
    presenter: GetTimeseriesPresenter

    def handle_request(self, request: Request) -> Response:
        use_case_request = self.controller.parse_request(request)
        use_case_response = self.use_case.get_timeseries(use_case_request)
        view_model = self.presenter.present_timeseries_as_json_response(
            use_case_response
        )
        return jsonify(view_model.json_object)
