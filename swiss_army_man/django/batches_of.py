class BatchesOf():
    # with batch in batches_of(Session.objects.all(), 1000):
    #   do_something(batch) # actually yields 1000 results instead of Django's iterator
    @staticmethod
    def batches_of(queryset, batch_size=1000):
        """Generator function that yields batches of objects from a queryset."""
        batch = []
        for obj in queryset.iterator():
            batch.append(obj)
            if len(batch) >= batch_size:
                yield batch
                batch = []  # Reset batch list after yielding
        if batch:  # Yield any remaining objects in the last batch
            yield batch