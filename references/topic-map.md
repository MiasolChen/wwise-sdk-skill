# Wwise SDK Topic Map

Paths are relative to the resolved SDK root. Layouts can differ by Wwise
version and platform, so verify that each path exists before relying on it.

| Topic | Start Here | Useful Search Terms |
| --- | --- | --- |
| SDK version | `include/AK/AkWwiseSDKVersion.h` | `AK_WWISESDK_VERSION` |
| Initialization and termination | `include/AK/SoundEngine/Common/AkSoundEngine.h`, platform headers under `include/AK/SoundEngine/Platforms` | `Init`, `Term`, `GetDefaultInitSettings` |
| Events and playback | `include/AK/SoundEngine/Common/AkSoundEngine.h` | `PostEvent`, `ExecuteActionOnEvent`, `StopPlayingID` |
| Callbacks | `include/AK/SoundEngine/Common/AkCallbackTypes.h` | `AkCallbackType`, `AkCallbackInfo`, `AkCallbackFunc` |
| Game objects and listeners | `include/AK/SoundEngine/Common/AkSoundEngine.h` | `RegisterGameObj`, `SetPosition`, `SetListeners` |
| RTPCs, states, and switches | `include/AK/SoundEngine/Common/AkSoundEngine.h` | `SetRTPCValue`, `SetState`, `SetSwitch` |
| SoundBanks and media | `include/AK/SoundEngine/Common/AkSoundEngine.h` | `LoadBank`, `UnloadBank`, `SetMedia` |
| Queries | `include/AK/SoundEngine/Common/AkQueryParameters.h` | API or type name |
| Memory manager | `include/AK/SoundEngine/Common/AkMemoryMgr.h` | `MemoryMgr`, `AkMemSettings` |
| Stream manager and file I/O | `include/AK/SoundEngine/Common/AkStreamMgrModule.h`, `samples/SoundEngine` | `StreamMgr`, `LowLevelIO`, `AkDeviceSettings` |
| Spatial Audio | `include/AK/SpatialAudio/Common/AkSpatialAudio.h` | `RegisterRoom`, `RegisterPortal`, `SetGeometry`, `SetImageSource` |
| Runtime plug-ins | `include/AK/SoundEngine/Common/IAkPlugin.h`, `include/AK/Plugin` | interface name, `AK_IMPLEMENT_PLUGIN_FACTORY` |
| Authoring plug-ins | `include/AK/Wwise/Plugin` | interface name, `PluginInfo` |
| WAAPI client | `include/AK/WwiseAuthoringAPI` | `Connect`, `Call`, `Subscribe`, URI name |
| Communication and Profiler | `include/AK/Comm` | `Comm`, `Init`, `Term` |
| Music engine | `include/AK/MusicEngine` when present | `MusicEngine`, `GetPlayingSegmentInfo` |
| Dynamic dialogue | search `include/AK` | `DynamicDialogue`, `ResolveDialogueEvent` |
| Dynamic sequences | search `include/AK` | `DynamicSequence`, `Open`, `LockPlaylist` |
| Integration examples | `samples/IntegrationDemo` | API or feature name |
| Plug-in examples | `samples/Plugins` | plug-in type or interface name |
| Official SDK documentation | `Help/WwiseSDK-Windows.chm`, localized files under `Help/<language>` | API name, guide title, feature name |
| Full Wwise implementation source | `source/SoundEngine`, `source/SpatialAudio`, `source/StreamManager`, platform and build directories, plus other installed components | symbol, internal class, subsystem name |

## Layout Differences

Older skills often assume paths such as `include/AK/SoundEngine/AkSoundEngine.h`.
Recent SDKs commonly place the declaration under `SoundEngine/Common`. Search
by filename or symbol rather than treating one release's layout as universal.

Some platform and optional package content is installed only when selected in
the Audiokinetic Launcher. A missing directory is not proof that an API never
exists; report the inspected installation and package set.

`Help` contains Audiokinetic's locally installed SDK documentation, commonly as
CHM files on Windows. The helper's `--area help` mode extracts CHM content to a
temporary directory for searching and removes it afterward. `source` is the
Wwise implementation source tree, not sample code. It can contain the complete
available Sound Engine and related subsystem implementations for users with
source access. Its exact components depend on the installed version, platform,
packages, and entitlements.

Common Windows layouts include both newer per-user installations and older
Launcher installations such as
`C:/Program Files (x86)/Audiokinetic/Wwise <version>/SDK/source`. Resolve the SDK
root first, then search `source` recursively rather than depending on one fixed
absolute path.
