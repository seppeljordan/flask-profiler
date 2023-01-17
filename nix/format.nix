{ writeShellApplication, isort, nixpkgs-fmt, black }:

writeShellApplication {
  name = "format-source";
  text = ''
    isort .
    black .
    nixpkgs-fmt .
  '';
  runtimeInputs = [ isort black nixpkgs-fmt ];
}
