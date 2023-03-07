# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import proto.command_pb2 as command__pb2
import proto.connect_pb2 as connect__pb2
import proto.message_pb2 as message__pb2
import proto.state_pb2 as state__pb2


class GrpcBotApiStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Connect = channel.unary_unary(
                '/GrpcBotApi/Connect',
                request_serializer=connect__pb2.ConnectRequest.SerializeToString,
                response_deserializer=connect__pb2.ConnectResponse.FromString,
                )
        self.Disconnect = channel.unary_unary(
                '/GrpcBotApi/Disconnect',
                request_serializer=connect__pb2.DisconnectRequest.SerializeToString,
                response_deserializer=connect__pb2.DisconnectResponse.FromString,
                )
        self.GetGame = channel.unary_unary(
                '/GrpcBotApi/GetGame',
                request_serializer=state__pb2.GetGameRequest.SerializeToString,
                response_deserializer=state__pb2.GetGameResponse.FromString,
                )
        self.GetActor = channel.unary_unary(
                '/GrpcBotApi/GetActor',
                request_serializer=state__pb2.GetActorRequest.SerializeToString,
                response_deserializer=state__pb2.GetActorResponse.FromString,
                )
        self.SubscribeMessages = channel.unary_stream(
                '/GrpcBotApi/SubscribeMessages',
                request_serializer=message__pb2.SubscribeMessagesRequest.SerializeToString,
                response_deserializer=message__pb2.SubscribeMessagesResponse.FromString,
                )
        self.SendMessage = channel.unary_unary(
                '/GrpcBotApi/SendMessage',
                request_serializer=message__pb2.SendMessageRequest.SerializeToString,
                response_deserializer=message__pb2.SendMessageResponse.FromString,
                )
        self.TrialVote = channel.unary_unary(
                '/GrpcBotApi/TrialVote',
                request_serializer=command__pb2.TargetRequest.SerializeToString,
                response_deserializer=command__pb2.TargetResponse.FromString,
                )
        self.LynchVote = channel.unary_unary(
                '/GrpcBotApi/LynchVote',
                request_serializer=command__pb2.BoolVoteRequest.SerializeToString,
                response_deserializer=command__pb2.BoolVoteResponse.FromString,
                )
        self.SkipVote = channel.unary_unary(
                '/GrpcBotApi/SkipVote',
                request_serializer=command__pb2.BoolVoteRequest.SerializeToString,
                response_deserializer=command__pb2.BoolVoteResponse.FromString,
                )
        self.DayTarget = channel.unary_unary(
                '/GrpcBotApi/DayTarget',
                request_serializer=command__pb2.TargetRequest.SerializeToString,
                response_deserializer=command__pb2.TargetResponse.FromString,
                )
        self.NightTarget = channel.unary_unary(
                '/GrpcBotApi/NightTarget',
                request_serializer=command__pb2.TargetRequest.SerializeToString,
                response_deserializer=command__pb2.TargetResponse.FromString,
                )


class GrpcBotApiServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Connect(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Disconnect(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetGame(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetActor(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SubscribeMessages(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendMessage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TrialVote(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def LynchVote(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SkipVote(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DayTarget(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NightTarget(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_GrpcBotApiServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Connect': grpc.unary_unary_rpc_method_handler(
                    servicer.Connect,
                    request_deserializer=connect__pb2.ConnectRequest.FromString,
                    response_serializer=connect__pb2.ConnectResponse.SerializeToString,
            ),
            'Disconnect': grpc.unary_unary_rpc_method_handler(
                    servicer.Disconnect,
                    request_deserializer=connect__pb2.DisconnectRequest.FromString,
                    response_serializer=connect__pb2.DisconnectResponse.SerializeToString,
            ),
            'GetGame': grpc.unary_unary_rpc_method_handler(
                    servicer.GetGame,
                    request_deserializer=state__pb2.GetGameRequest.FromString,
                    response_serializer=state__pb2.GetGameResponse.SerializeToString,
            ),
            'GetActor': grpc.unary_unary_rpc_method_handler(
                    servicer.GetActor,
                    request_deserializer=state__pb2.GetActorRequest.FromString,
                    response_serializer=state__pb2.GetActorResponse.SerializeToString,
            ),
            'SubscribeMessages': grpc.unary_stream_rpc_method_handler(
                    servicer.SubscribeMessages,
                    request_deserializer=message__pb2.SubscribeMessagesRequest.FromString,
                    response_serializer=message__pb2.SubscribeMessagesResponse.SerializeToString,
            ),
            'SendMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.SendMessage,
                    request_deserializer=message__pb2.SendMessageRequest.FromString,
                    response_serializer=message__pb2.SendMessageResponse.SerializeToString,
            ),
            'TrialVote': grpc.unary_unary_rpc_method_handler(
                    servicer.TrialVote,
                    request_deserializer=command__pb2.TargetRequest.FromString,
                    response_serializer=command__pb2.TargetResponse.SerializeToString,
            ),
            'LynchVote': grpc.unary_unary_rpc_method_handler(
                    servicer.LynchVote,
                    request_deserializer=command__pb2.BoolVoteRequest.FromString,
                    response_serializer=command__pb2.BoolVoteResponse.SerializeToString,
            ),
            'SkipVote': grpc.unary_unary_rpc_method_handler(
                    servicer.SkipVote,
                    request_deserializer=command__pb2.BoolVoteRequest.FromString,
                    response_serializer=command__pb2.BoolVoteResponse.SerializeToString,
            ),
            'DayTarget': grpc.unary_unary_rpc_method_handler(
                    servicer.DayTarget,
                    request_deserializer=command__pb2.TargetRequest.FromString,
                    response_serializer=command__pb2.TargetResponse.SerializeToString,
            ),
            'NightTarget': grpc.unary_unary_rpc_method_handler(
                    servicer.NightTarget,
                    request_deserializer=command__pb2.TargetRequest.FromString,
                    response_serializer=command__pb2.TargetResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'GrpcBotApi', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class GrpcBotApi(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Connect(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/Connect',
            connect__pb2.ConnectRequest.SerializeToString,
            connect__pb2.ConnectResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Disconnect(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/Disconnect',
            connect__pb2.DisconnectRequest.SerializeToString,
            connect__pb2.DisconnectResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetGame(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/GetGame',
            state__pb2.GetGameRequest.SerializeToString,
            state__pb2.GetGameResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetActor(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/GetActor',
            state__pb2.GetActorRequest.SerializeToString,
            state__pb2.GetActorResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SubscribeMessages(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/GrpcBotApi/SubscribeMessages',
            message__pb2.SubscribeMessagesRequest.SerializeToString,
            message__pb2.SubscribeMessagesResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/SendMessage',
            message__pb2.SendMessageRequest.SerializeToString,
            message__pb2.SendMessageResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def TrialVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/TrialVote',
            command__pb2.TargetRequest.SerializeToString,
            command__pb2.TargetResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def LynchVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/LynchVote',
            command__pb2.BoolVoteRequest.SerializeToString,
            command__pb2.BoolVoteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SkipVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/SkipVote',
            command__pb2.BoolVoteRequest.SerializeToString,
            command__pb2.BoolVoteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DayTarget(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/DayTarget',
            command__pb2.TargetRequest.SerializeToString,
            command__pb2.TargetResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NightTarget(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/GrpcBotApi/NightTarget',
            command__pb2.TargetRequest.SerializeToString,
            command__pb2.TargetResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
