# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: state.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bstate.proto\"8\n\x06Player\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0e\n\x06is_bot\x18\x02 \x01(\x08\x12\x10\n\x08is_human\x18\x03 \x01(\x08\"u\n\x04Role\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0b\x61\x66\x66iliation\x18\x02 \x01(\t\x12\x18\n\x10role_description\x18\x03 \x01(\t\x12\x1a\n\x12\x61\x63tion_description\x18\x04 \x01(\t\x12\x14\n\x0c\x61\x62ility_uses\x18\x05 \x01(\x05\"G\n\x05\x41\x63tor\x12\x17\n\x06player\x18\x01 \x01(\x0b\x32\x07.Player\x12\x13\n\x04role\x18\x02 \x01(\x0b\x32\x05.Role\x12\x10\n\x08is_alive\x18\x03 \x01(\x08\"\x97\x01\n\x04Game\x12\x12\n\ngame_phase\x18\x01 \x01(\t\x12\x12\n\nturn_phase\x18\x02 \x01(\t\x12\x13\n\x0bturn_number\x18\x03 \x01(\x05\x12\x16\n\x06\x61\x63tors\x18\x04 \x03(\x0b\x32\x06.Actor\x12\x1d\n\tgraveyard\x18\x05 \x03(\x0b\x32\n.Tombstone\x12\x1b\n\x08tribunal\x18\x06 \x01(\x0b\x32\t.Tribunal\"^\n\tTombstone\x12\x17\n\x06player\x18\x01 \x01(\x0b\x32\x07.Player\x12\x0f\n\x07\x65pitaph\x18\x02 \x01(\t\x12\x12\n\nturn_phase\x18\x03 \x01(\t\x12\x13\n\x0bturn_number\x18\x04 \x01(\x05\"3\n\tVoteCount\x12\x17\n\x06player\x18\x01 \x01(\x0b\x32\x07.Player\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\"\xec\x01\n\x08Tribunal\x12\r\n\x05state\x18\x01 \x01(\t\x12\x1f\n\x0btrial_votes\x18\x02 \x03(\x0b\x32\n.VoteCount\x12\x1f\n\x0blynch_votes\x18\x03 \x03(\x0b\x32\n.VoteCount\x12\x12\n\nskip_votes\x18\x04 \x01(\x05\x12\x18\n\x08on_trial\x18\x05 \x01(\x0b\x32\x06.Actor\x12\x15\n\x05judge\x18\x06 \x01(\x0b\x32\x06.Actor\x12\x15\n\x05mayor\x18\x07 \x01(\x0b\x32\x06.Actor\x12\x12\n\ntrial_type\x18\x08 \x01(\t\x12\x1f\n\x0bvote_counts\x18\t \x03(\x0b\x32\n.VoteCount\"3\n\x0eGetGameRequest\x12\x11\n\ttimestamp\x18\x01 \x01(\x02\x12\x0e\n\x06\x62ot_id\x18\x02 \x01(\t\"9\n\x0fGetGameResponse\x12\x11\n\ttimestamp\x18\x01 \x01(\x02\x12\x13\n\x04game\x18\x02 \x01(\x0b\x32\x05.Game\"[\n\x0fGetActorRequest\x12\x11\n\ttimestamp\x18\x01 \x01(\x02\x12\x10\n\x06\x62ot_id\x18\x02 \x01(\tH\x00\x12\x15\n\x0bplayer_name\x18\x03 \x01(\tH\x00\x42\x0c\n\nidentifier\"<\n\x10GetActorResponse\x12\x11\n\ttimestamp\x18\x01 \x01(\x02\x12\x15\n\x05\x61\x63tor\x18\x02 \x01(\x0b\x32\x06.Actorb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'state_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PLAYER._serialized_start=15
  _PLAYER._serialized_end=71
  _ROLE._serialized_start=73
  _ROLE._serialized_end=190
  _ACTOR._serialized_start=192
  _ACTOR._serialized_end=263
  _GAME._serialized_start=266
  _GAME._serialized_end=417
  _TOMBSTONE._serialized_start=419
  _TOMBSTONE._serialized_end=513
  _VOTECOUNT._serialized_start=515
  _VOTECOUNT._serialized_end=566
  _TRIBUNAL._serialized_start=569
  _TRIBUNAL._serialized_end=805
  _GETGAMEREQUEST._serialized_start=807
  _GETGAMEREQUEST._serialized_end=858
  _GETGAMERESPONSE._serialized_start=860
  _GETGAMERESPONSE._serialized_end=917
  _GETACTORREQUEST._serialized_start=919
  _GETACTORREQUEST._serialized_end=1010
  _GETACTORRESPONSE._serialized_start=1012
  _GETACTORRESPONSE._serialized_end=1072
# @@protoc_insertion_point(module_scope)
