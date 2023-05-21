{ lib
, buildPythonPackage
, flask
, flask-httpauth
, flask-testing
, hypothesis
, pytestCheckHook
, setuptools
, typing-extensions
}:
buildPythonPackage rec {
  pname = "flask_profiler";
  version = "master";
  src = ../.;
  buildInputs = [ setuptools ];
  propagatedBuildInputs = [ flask-httpauth flask typing-extensions ];
  checkInputs = [ flask-testing pytestCheckHook hypothesis ];
  format = "pyproject";
  meta = with lib; { license = licenses.mit; };
}
