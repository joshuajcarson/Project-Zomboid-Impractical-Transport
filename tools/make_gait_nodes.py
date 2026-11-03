"""Writes the movement anim nodes of every transport: walk, run and sprint, each in three speed tiers (the clips come from tools/blender/pogo_hop.py and
tricycle_ride.py), plus the tricycle's idle node. The Lua sets <Name>Active (bool) and <Name>Tier (string "0", "1", "2"); the run and sprint nodes
sit in the engine's run and sprint states, walk in movement. Other hand-written nodes (the pogo's idle, mount and dismount) are not touched.
  python tools/make_gait_nodes.py"""
import pathlib
BASE = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/AnimSets/player"
NODE = """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>{name}</m_Name>
	<m_AnimName>{clip}</m_AnimName>
	<m_Priority>10</m_Priority>
	<m_ConditionPriority>{cprio}</m_ConditionPriority>
	<m_deferredBoneAxis>Y</m_deferredBoneAxis>
	<m_BlendTime>0.40</m_BlendTime>
	<m_SyncTrackingEnabled>false</m_SyncTrackingEnabled>
	<m_Conditions>
		<m_Name>{var}Active</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
	<m_Conditions>
		<m_Name>isMoving</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>{moving}</m_Value>
	</m_Conditions>
{tier}{sprint}</animNode>
"""
TIER = """	<m_Conditions>
		<m_Name>{var}Tier</m_Name>
		<m_Type>STRING</m_Type>
		<m_StringValue>{level}</m_StringValue>
	</m_Conditions>
"""
# The Lua sets <Name>Sprint when the sprint key is held but the engine stayed in the run state (see ImpracticalTransport.lua): the run folder then plays the
# sprint clip. Only the pogo has a sprint clip of its own; the others sprint with the run clip, so they need no such node.
SPRINT = """	<m_Conditions>
		<m_Name>{var}Sprint</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>{value}</m_Value>
	</m_Conditions>
"""
# per transport: variable prefix, clip name prefix, and for each gait (folder, file stem, clip suffix)
TRANSPORTS = {
    "Pogo": dict(clip="Bob_PogoHop", gaits=(("movement", "walk_pogo", ""), ("run", "run_pogo", "Run"), ("sprint", "defaultSprint_pogo", "Sprint"))),
    "Trike": dict(clip="Bob_TrikeRide", gaits=(("movement", "walk_trike", ""), ("run", "run_trike", "Run"), ("sprint", "sprint_trike", "Run")), idle="Bob_TrikeIdle"),
    "Skates": dict(tiers=("", "T1", "T2", "F"), clip="Bob_SkateGlide", gaits=(("movement", "walk_skates", ""), ("run", "run_skates", "Run"), ("sprint", "sprint_skates", "Run")), idle="Bob_SkateIdle"),
    "Uni": dict(clip="Bob_UniRide", gaits=(("movement", "walk_uni", ""), ("run", "run_uni", "Run"), ("sprint", "sprint_uni", "Run")), idle="Bob_UniIdle"),
}
# coast nodes (idle state): the rider glides on after stopping, one clip per gait and tier so the glide starts at the speed the rider was going
COAST = """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>{name}</m_Name>
	<m_AnimName>{clip}</m_AnimName>
	<m_Priority>20</m_Priority>
	<m_ConditionPriority>20</m_ConditionPriority>
	<m_deferredBoneAxis>Y</m_deferredBoneAxis>
	<m_BlendTime>0.20</m_BlendTime>
	<m_SyncTrackingEnabled>false</m_SyncTrackingEnabled>
	<m_Conditions>
		<m_Name>SkatesActive</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
	<m_Conditions>
		<m_Name>SkatesCoast</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
	<m_Conditions>
		<m_Name>SkatesCoastGait</m_Name>
		<m_Type>STRING</m_Type>
		<m_StringValue>{gait}</m_StringValue>
	</m_Conditions>
{tier}</animNode>
"""
for gait in ("", "Run"):
    for level, tier in enumerate(("", "T1", "T2", "F")):
        name = "coast_skates" + ("_run" if gait else "") + ("" if not level else f"_t{level}")
        text = COAST.format(name=name, clip=f"Bob_SkateCoast{gait}{tier}", gait=gait or "walk", tier=TIER.format(var="Skates", level=level))
        (BASE / "idle" / (name + ".xml")).write_text(text, encoding="utf-8", newline="\n"); print("wrote idle", name)
for var, t in TRANSPORTS.items():
    for folder, stem, suffix in t["gaits"]:
        for level, tier in enumerate(t.get("tiers", ("", "T1", "T2"))):
            file = stem + ("" if not level else f"_t{level}")
            name = file.replace("defaultSprint_pogo", "sprint_pogo")
            def write(name, file, clip, sprint="", cprio=10):
                text = NODE.format(name=name, clip=clip, var=var, moving="true", tier=TIER.format(var=var, level=level), sprint=sprint, cprio=cprio)
                (BASE / folder / (file + ".xml")).write_text(text, encoding="utf-8", newline="\n"); print("wrote", folder, file)
            forced = var == "Pogo" and folder == "run"
            write(name, file, f"{t['clip']}{suffix}{tier}", SPRINT.format(var=var, value="false") if forced else "")
            if forced: write(name.replace("run_", "runsprint_"), file.replace("run_", "runsprint_"), f"{t['clip']}Sprint{tier}", SPRINT.format(var=var, value="true"), 11)
    if "idle" in t:
        text = NODE.format(name=f"idle_{var.lower()}", clip=t["idle"], var=var, moving="false", tier="", sprint="", cprio=10)
        (BASE / "idle" / f"idle_{var.lower()}.xml").write_text(text, encoding="utf-8", newline="\n"); print("wrote idle", var)
