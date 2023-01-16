{ lib, buildPythonPackage, flask, flask-httpauth, flask-testing, hypothesis
, pytestCheckHook, setuptools }:
buildPythonPackage rec {
  pname = "flask_profiler";
  version = "master";
  src = ../.;
  buildInputs = [ setuptools ];
  propagatedBuildInputs = [ flask-httpauth flask ];
  checkInputs = [ flask-testing pytestCheckHook hypothesis ];
  format = "pyproject";
  meta = with lib; { license = licenses.mit; };
}
