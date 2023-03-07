from objectref.objectloc.dummy import DummyObjectLocationDetector


if __name__ == '__main__':
    print("Location", DummyObjectLocationDetector().get_location(None, None))
