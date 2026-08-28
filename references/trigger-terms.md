# Wwise Trigger Terms

Use this list to decide whether a request is Wwise-specific. Any term in the
positive lists is an explicit signal. Terms in the negative list are not, unless
the user also names Wwise.

## Official URL Signal

An Audiokinetic **documentation** URL is an unconditional Wwise signal, even
when the user's entire message is only the URL. A URL qualifies when the host is
`audiokinetic.com` or one of its subdomains **and** the path contains
`library` or `public-library`:

- `https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/?source=SDK&id=soundengine_events`
- `https://www.audiokinetic.com/library/edge/?source=SDK&id=soundengine_events`

Other paths on the same host are not documentation and have no local
counterpart: `/community/` (Q&A, blog, forum), `/products/`, `/pricing/`,
`/news/`, `/events/`, `/courses/`, and marketing pages. These are not a trigger.

For how such a URL is resolved, see the **Documentation URLs** section of
`SKILL.md`.

## Product And Tooling Names

Wwise, Audiokinetic, Wwise Launcher, Wwise Authoring, WAAPI, Wwise Authoring API,
Wwise SDK, SoundBank, Wwise Project, Work Unit, Wwise Profiler, Wwise
Communication, Integration Demo, Wwise Unity Integration, Wwise Unreal
Integration, WAQL.

## Product Concepts

These are Wwise concepts when named as Wwise features. Several are generic words
on their own, so treat them as signals only in a Wwise context.

Event, Action, SoundBank, Media, RTPC, Real-Time Parameter Control, State, State
Group, Switch, Switch Group, Trigger, Game Object, Listener, Emitter, Game
Parameter, Actor-Mixer, Blend Container, Random Container, Sequence Container,
Switch Container, Music Segment, Music Playlist, Music Switch Container,
Interactive Music, Dynamic Dialogue, Dialogue Event, Dynamic Sequence, Audio Bus,
Auxiliary Bus, Auxiliary Send, Game-defined Auxiliary Send, Effect ShareSet,
Attenuation, Virtual Voice, Playback Limit, Room, Portal, Geometry, Diffraction,
Reflect, Acoustic Texture, Spatial Audio, Audio Objects, Sink, ShareSet.

## SDK Symbols And Prefixes

Any identifier with these prefixes is a strong signal: `AK::`, `AK_`, `Ak`,
`IAk`, `CAk`.

Frequently referenced symbols verified in the SDK headers:

| Area | Symbols |
| --- | --- |
| Namespaces and results | `AK::SoundEngine`, `AK::MusicEngine`, `AK::SpatialAudio`, `AK::StreamMgr`, `AK::Comm`, `AKRESULT`, `AK_Success`, `AK_Fail` |
| Lifecycle | `AkInitSettings`, `AkPlatformInitSettings`, `AkStreamMgrSettings`, `AkDeviceSettings`, `AkMemSettings` |
| Playback | `PostEvent`, `ExecuteActionOnEvent`, `StopPlayingID`, `StopAll`, `PostTrigger`, `AkPlayingID` |
| Game objects | `RegisterGameObj`, `UnregisterGameObj`, `SetPosition`, `SetListeners`, `AkGameObjectID`, `AkSoundPosition` |
| Parameters | `SetRTPCValue`, `SetState`, `SetSwitch`, `SetGameObjectAuxSendValues`, `AkAuxBusID`, `AkRtpcID` |
| Banks | `LoadBank`, `UnloadBank`, `PrepareEvent`, `PrepareBank`, `SetMedia`, `AkBankID` |
| Identifiers | `AkUniqueID`, `AkStateID`, `AkSwitchStateID`, `AkChannelConfig`, `AkAudioObjectID` |
| Callbacks | `AkCallbackType`, `AkCallbackInfo`, `AkCallbackFunc`, `AkEventCallbackInfo`, `AkMusicSyncCallbackInfo` |
| Spatial Audio | `SetRoom`, `SetPortal`, `SetGeometry`, `SetGeometryInstance`, `AkRoomID`, `AkRoomParams`, `AkPortalID`, `AkPortalParams`, `AkImageSourceSettings` |
| Streaming | `IAkStreamMgr`, `AK::IAkStdStream`, `AK::IAkAutoStream`, `AkFileSystemFlags` |
| Plug-ins | `IAkEffectPlugin`, `IAkSourcePlugin`, `IAkPluginParam`, `AK_IMPLEMENT_PLUGIN_FACTORY`, `AkAudioBuffer`, `AkAudioObject` |
| Authoring and WAAPI | `AK::WwiseAuthoringAPI`, `ak.wwise.core.object.get`, `ak.soundengine.postEvent` |

Header, file, and path signals: `AkSoundEngine.h`, `AkCallbackTypes.h`,
`AkSpatialAudio.h`, `IAkPlugin.h`, `AkWwiseSDKVersion.h`, `include/AK/`,
`SDK/Help`, `WwiseSDK-Windows.chm`, `Wwise_IDs.h`, `SoundbanksInfo.json`,
`*.bnk`, `*.wwu`, `*.wproj`, and any Audiokinetic documentation URL under
`library` or `public-library`.

## Not Triggers On Their Own

Do not activate for these unless the user also names Wwise or a Wwise symbol.

- General audio: sound design, mixing, mastering, loudness, LUFS, EQ,
  compression, reverb, occlusion, obstruction, attenuation, 3D audio, ambisonics,
  HRTF, spatial audio.
- Audio programming: DSP, FFT, convolution, resampling, ring buffer, audio
  callback, buffer size, sample rate, channel layout, latency, dithering.
- Other middleware and APIs: FMOD, FMOD Studio, CRIWARE, ADX2, Elias, Unity
  `AudioSource`, Unity `AudioMixer`, Unreal MetaSounds, Unreal Audio Engine,
  Web Audio API, XAudio2, WASAPI, ASIO, PortAudio, miniaudio, OpenAL, SDL_mixer,
  JUCE, Steam Audio, Oculus Audio, Resonance Audio.
- Formats and tools: WAV, Ogg Vorbis, Opus, FLAC, Reaper, Pro Tools, Audacity,
  iZotope RX.

Note the overlap: Wwise uses common words such as Event, Bus, State, and Spatial
Audio. The deciding factor is whether the user is asking about Wwise's
implementation of the concept, not whether the word appears.
