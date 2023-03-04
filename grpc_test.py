"""
I have no idea what I'm doing
"""
import asyncio
import time

from grpc import aio
from grpc import RpcError
from proto import connect_pb2
from proto import connect_pb2_grpc
from proto import state_pb2
from proto import state_pb2_grpc

BIND = 'localhost:50051'


class ManageSessionServicer(connect_pb2_grpc.ManageSessionServicer):
    """
    hehehehe
    """

    def Connect(self, request, context):
        raise ValueError("What the hell")
        #return connect_pb2.ConnectResponse(timestamp=time.time(), bot_name="HELLO BABE", bot_id='12345')

    def Disconnect(self, request, context):
        return connect_pb2.DisconnectResponse(timestamp=time.time(), success=True)
        #raise ValueError("")


async def client():
    async with aio.insecure_channel(BIND) as channel:
        stub = connect_pb2_grpc.ManageSessionStub(channel)
        try:
            response = await stub.Connect(connect_pb2.ConnectRequest(timestamp=time.time()))
            print(f"got a connect response: {response}")
        except RpcError as error:
            print(f"Error response: {repr(error)}")


_cleanup_coroutines = []
async def server():
    server = aio.server()
    connect_pb2_grpc.add_ManageSessionServicer_to_server(ManageSessionServicer(), server)
    server.add_insecure_port(BIND)
    print("RUNNING A GRPC SERVER OMFGGGGG")
    await server.start()

    async def server_graceful_shutdown():
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    global _cleanup_coroutines
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["server", "client"])
    args = p.parse_args()
    if args.command == "client":
        asyncio.run(client())
    elif args.command == "server":
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(server())
        except:
            print("Shutting down.")
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
    else:
        raise ValueError(f"wtf input is {args.command}")
