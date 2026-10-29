(function () {
  "use strict";
  var agent = document.getElementById("agent-select");
  var profile = document.getElementById("profile-select");
  var command = document.getElementById("install-command");
  var button = document.getElementById("copy-command");
  var status = document.getElementById("copy-status");
  if (!agent || !profile || !command || !button || !status) return;
  function updateCommand() {
    command.textContent = "python3 tools/install_portable.py --agent " + agent.value +
      " --scope user --profile " + profile.value + " --dry-run";
    status.textContent = "";
  }
  agent.addEventListener("change", updateCommand);
  profile.addEventListener("change", updateCommand);
  button.addEventListener("click", function () {
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      status.textContent = "Clipboard unavailable: select and copy the command above.";
      return;
    }
    navigator.clipboard.writeText(command.textContent).then(function () {
      status.textContent = "Preview command copied.";
    }).catch(function () {
      status.textContent = "Copy unavailable: select and copy the command above.";
    });
  });
  updateCommand();
}());
