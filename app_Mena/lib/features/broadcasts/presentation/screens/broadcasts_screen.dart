import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/theme/app_colors.dart';

final broadcastsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get('/broadcasts');
  final list = response.data as List<dynamic>;
  return list.cast<Map<String, dynamic>>();
});

class BroadcastsScreen extends ConsumerWidget {
  const BroadcastsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final broadcastsAsync = ref.watch(broadcastsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Broadcast Announcements', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => ref.invalidate(broadcastsProvider),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(broadcastsProvider.future),
        child: broadcastsAsync.when(
          data: (broadcasts) {
            if (broadcasts.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.campaign_outlined, size: 64, color: Colors.grey.shade400),
                    const SizedBox(height: 12),
                    const Text(
                      'No Broadcast Announcements',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'All current branch and enterprise notices will appear here.',
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                  ],
                ),
              );
            }

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: broadcasts.length,
              separatorBuilder: (context, index) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final b = broadcasts[index];
                final isUrgent = (b['priority'] as String?)?.toLowerCase() == 'urgent';

                return Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: isUrgent
                        ? const BorderSide(color: AppColors.critical, width: 1.5)
                        : BorderSide.none,
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            CircleAvatar(
                              backgroundColor: isUrgent
                                  ? AppColors.critical.withValues(alpha: 0.2)
                                  : AppColors.forestGreen.withValues(alpha: 0.2),
                              child: Icon(
                                isUrgent ? Icons.warning_amber_rounded : Icons.campaign_rounded,
                                color: isUrgent ? AppColors.critical : AppColors.forestGreen,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    b['title'] as String? ?? 'Notice',
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    'To: ${b['target_store_name'] ?? 'All Branches'}  •  From: ${b['created_by'] ?? 'System Admin'}',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            if (isUrgent)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppColors.critical.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: const Text(
                                  'URGENT',
                                  style: TextStyle(
                                    color: AppColors.critical,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 11,
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          b['message'] as String? ?? '',
                          style: const TextStyle(fontSize: 14, height: 1.4),
                        ),
                        const SizedBox(height: 10),
                        Align(
                          alignment: Alignment.centerRight,
                          child: Text(
                            (b['created_at'] as String?)?.split('T').first ?? '',
                            style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, stackTrace) => Center(child: Text('Failed to load broadcasts: $e')),
        ),
      ),
    );
  }
}
