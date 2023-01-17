{
  description = "flask-profiler";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    let
      systemDependent = flake-utils.lib.eachSystem supportedSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ self.overlays.default ];
          };
          python = pkgs.python310;
          pythonEnv =
            python.withPackages (p: [ p.mypy p.flake8 p.isort p.black ]
              ++ python.pkgs.flask-profiler.buildInputs
              ++ python.pkgs.flask-profiler.propagatedBuildInputs);
          format-source = pkgs.callPackage nix/format.nix { };
        in
        {
          formatter = format-source;
          packages = {
            default = python.pkgs.flask-profiler;
            inherit python format-source;
          };
          devShells.default = pkgs.mkShell {
            packages = with python.pkgs; [
              black
              coverage
              flake8
              isort
              mypy
              twine
              virtualenv
            ];
            inputsFrom = [ python.pkgs.flask-profiler ];
          };
          checks = {
            inherit format-source;
            black-check = pkgs.runCommand "black-check" { } ''
              cd ${self}
              ${pythonEnv}/bin/black --check .
              mkdir $out
            '';
            isort-check = pkgs.runCommand "isort-check" { } ''
              cd ${self}
              ${pythonEnv}/bin/isort --check .
              mkdir $out
            '';
            flake8-check = pkgs.runCommand "flake8-check" { } ''
              cd ${self}
              ${pythonEnv}/bin/flake8
              mkdir $out
            '';
            mypy-check = pkgs.runCommand "mypy-check" { } ''
              cd ${self}
              ${pythonEnv}/bin/mypy
              mkdir $out
            '';
            python39-package = pkgs.python39.pkgs.flask-profiler;
            python310-package = pkgs.python310.pkgs.flask-profiler;
          };
        });
      supportedSystems = flake-utils.lib.defaultSystems;
      systemIndependent = {
        overlays.default = final: prev: {
          pythonPackagesExtensions = prev.pythonPackagesExtensions
            ++ [ (import nix/pythonPackages.nix) ];
        };
      };
    in
    systemDependent // systemIndependent;
}
