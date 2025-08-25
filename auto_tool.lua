-- auto_tool_start.lua

local READY_FILE = "controller_ready.txt"

-- Start emulator paused and open toolbox
for i = 1, 10 do
  emu.frameadvance()
end

client.opentoolbox()
client.pause()


while true do
  emu.frameadvance()
  local f = io.open(READY_FILE, "r")

  if f then
    -- File exists → game runs
    f:close()
    client.unpause()
  else
    -- File missing → break out
    break
  end
end

-- Ensure unpaused on exit
client.unpause()
console.log("Lua script exiting.")
