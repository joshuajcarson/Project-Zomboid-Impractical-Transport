"""Writes the pogo movement anim nodes: walk, run and sprint, each in three speed tiers (see GAITS/TIERS in tools/blender/pogo_hop.py).
The Lua sets the string variable PogoTier ("0", "1", "2"); the run and sprint nodes sit in the engine's run and sprint states, walk in movement.
  python tools/make_gait_nodes.py"""
import pathlib
BASE = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/AnimSets/player"
NODE = """<?xml version="1.0" encoding="utf-8"?>
<animNode>
	<m_Name>{name}</m_Name>
	<m_AnimName>Bob_PogoHop{gait}{tier}</m_AnimName>
	<m_Priority>10</m_Priority>
	<m_ConditionPriority>10</m_ConditionPriority>
	<m_deferredBoneAxis>Y</m_deferredBoneAxis>
	<m_BlendTime>0.40</m_BlendTime>
	<m_SyncTrackingEnabled>false</m_SyncTrackingEnabled>
	<m_Conditions>
		<m_Name>PogoActive</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
	<m_Conditions>
		<m_Name>isMoving</m_Name>
		<m_Type>BOOL</m_Type>
		<m_Value>true</m_Value>
	</m_Conditions>
	<m_Conditions>
		<m_Name>PogoTier</m_Name>
		<m_Type>STRING</m_Type>
		<m_StringValue>{level}</m_StringValue>
	</m_Conditions>
</animNode>
"""
FILES = {"": ("movement", "walk_pogo"), "Run": ("run", "run_pogo"), "Sprint": ("sprint", "defaultSprint_pogo")}
for gait, (folder, stem) in FILES.items():
    for level, tier in enumerate(("", "T1", "T2")):
        name = stem.replace("defaultSprint_pogo", "sprint_pogo") + ("" if not level else f"_t{level}")
        path = BASE / folder / (stem + ("" if not level else f"_t{level}") + ".xml")
        path.write_text(NODE.format(name=name, gait=gait, tier=tier, level=level), encoding="utf-8")
        print("wrote", path.name)
