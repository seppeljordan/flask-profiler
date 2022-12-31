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
          pythonEnv = pkgs.python3.withPackages (p:
            [ p.mypy p.flake8 p.isort p.black ]
            ++ pkgs.python3.pkgs.flask-profiler.buildInputs
            ++ pkgs.python3.pkgs.flask-profiler.propagatedBuildInputs);
        in {
          packages = { default = pkgs.python3.pkgs.flask-profiler; };
          devShells.default = pkgs.mkShell {
            packages = with pkgs.python3.pkgs; [
              black
              coverage
              flake8
              isort
              mypy
              twine
              virtualenv
            ];
            inputsFrom = [ pkgs.python3.pkgs.flask-profiler ];
          };
          checks = {
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
    in systemDependent // systemIndependent;
}
