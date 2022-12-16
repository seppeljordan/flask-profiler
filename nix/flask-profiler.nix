{ buildPythonPackage, flask-httpauth, flask, flask-testing
, pytestCheckHook, setuptools }:
buildPythonPackage rec {
  pname = "flask_profiler";
  version = "master";
  src = ../.;
  buildInputs = [ setuptools ];
  propagatedBuildInputs = [ flask-httpauth flask ];
  checkInputs = [ flask-testing pytestCheckHook ];
  format = "pyproject";
}
