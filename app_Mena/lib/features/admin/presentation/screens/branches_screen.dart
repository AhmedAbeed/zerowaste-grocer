import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/presentation/auth_providers.dart';

/// Admin branch list provider
final adminBranchesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get('/admin/branches');
  final list = response.data as List<dynamic>;
  return list.cast<Map<String, dynamic>>();
});

/// Admin global analytics provider
final adminGlobalAnalyticsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get('/admin/analytics/global');
  return response.data as Map<String, dynamic>;
});

class BranchesScreen extends ConsumerStatefulWidget {
  const BranchesScreen({super.key});

  @override
  ConsumerState<BranchesScreen> createState() => _BranchesScreenState();
}

class _BranchesScreenState extends ConsumerState<BranchesScreen> {
  void _openCreateBranchDialog() {
    final nameController = TextEditingController();
    final locationController = TextEditingController();
    final managerIdController = TextEditingController();
    final formKey = GlobalKey<FormState>();
    bool isSaving = false;

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.add_business_rounded, color: AppColors.forestGreen),
                SizedBox(width: 8),
                Text('Create Branch', style: TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            content: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextFormField(
                      controller: nameController,
                      decoration: const InputDecoration(
                        labelText: 'Branch Name',
                        hintText: 'e.g., Downtown Metro Superstore',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: locationController,
                      decoration: const InputDecoration(
                        labelText: 'Location / City',
                        hintText: 'e.g., Block 5, Central Ave',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: managerIdController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Manager User ID (Optional)',
                        hintText: 'e.g., 1',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: isSaving ? null : () => Navigator.of(dialogCtx).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: isSaving
                    ? null
                    : () async {
                        if (!formKey.currentState!.validate()) return;
                        final messenger = ScaffoldMessenger.of(context);
                        setDialogState(() => isSaving = true);
                        try {
                          final dio = ref.read(dioProvider);
                          final mgrId = int.tryParse(managerIdController.text.trim());
                          final payload = <String, dynamic>{
                            'name': nameController.text.trim(),
                            'location': locationController.text.trim(),
                            'manager_id': ?mgrId,
                          };
                          await dio.post('/admin/branches', data: payload);
                          ref.invalidate(adminBranchesProvider);
                          ref.invalidate(adminGlobalAnalyticsProvider);
                          ref.invalidate(storesProvider);
                          if (dialogCtx.mounted) {
                            Navigator.of(dialogCtx).pop();
                          }
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Branch created successfully!'),
                              backgroundColor: AppColors.safe,
                            ),
                          );
                        } catch (e) {
                          setDialogState(() => isSaving = false);
                          messenger.showSnackBar(
                            SnackBar(
                              content: Text('Failed: $e'),
                              backgroundColor: AppColors.critical,
                            ),
                          );
                        }
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.forestGreen,
                  foregroundColor: Colors.white,
                ),
                child: isSaving
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Create'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _openBroadcastDialog() {
    final titleController = TextEditingController();
    final messageController = TextEditingController();
    String priority = 'normal';
    int? targetStoreId;
    final formKey = GlobalKey<FormState>();
    bool isSending = false;

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setDialogState) {
          final branchesAsync = ref.watch(adminBranchesProvider);

          return AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.campaign_rounded, color: AppColors.forestGreen),
                SizedBox(width: 8),
                Text('Dispatch Broadcast', style: TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            content: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextFormField(
                      controller: titleController,
                      decoration: const InputDecoration(
                        labelText: 'Announcement Title',
                        hintText: 'e.g., Critical Spoilage Notice',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: messageController,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Message Body',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<int?>(
                      initialValue: targetStoreId,
                      decoration: const InputDecoration(
                        labelText: 'Target Branch',
                        border: OutlineInputBorder(),
                      ),
                      items: [
                        const DropdownMenuItem<int?>(
                          value: null,
                          child: Text('All Branches (Global Broadcast)'),
                        ),
                        if (branchesAsync.hasValue)
                          ...branchesAsync.value!.map((b) => DropdownMenuItem<int?>(
                                value: b['id'] as int,
                                child: Text('${b['name']} (#${b['id']})'),
                              )),
                      ],
                      onChanged: (v) => setDialogState(() => targetStoreId = v),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: priority,
                      decoration: const InputDecoration(
                        labelText: 'Priority Level',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'normal', child: Text('Normal Priority')),
                        DropdownMenuItem(value: 'urgent', child: Text('Urgent Alert')),
                      ],
                      onChanged: (v) => setDialogState(() => priority = v ?? 'normal'),
                    ),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: isSending ? null : () => Navigator.of(dialogCtx).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: isSending
                    ? null
                    : () async {
                        if (!formKey.currentState!.validate()) return;
                        final messenger = ScaffoldMessenger.of(context);
                        setDialogState(() => isSending = true);
                        try {
                          final dio = ref.read(dioProvider);
                          await dio.post('/admin/broadcast', data: {
                            'title': titleController.text.trim(),
                            'message': messageController.text.trim(),
                            'target_store_id': targetStoreId,
                            'priority': priority,
                          });
                          if (dialogCtx.mounted) {
                            Navigator.of(dialogCtx).pop();
                          }
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Broadcast sent successfully!'),
                              backgroundColor: AppColors.safe,
                            ),
                          );
                        } catch (e) {
                          setDialogState(() => isSending = false);
                          messenger.showSnackBar(
                            SnackBar(
                              content: Text('Failed: $e'),
                              backgroundColor: AppColors.critical,
                            ),
                          );
                        }
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.forestGreen,
                  foregroundColor: Colors.white,
                ),
                child: isSending
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Send Broadcast'),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final branchesAsync = ref.watch(adminBranchesProvider);
    final globalAsync = ref.watch(adminGlobalAnalyticsProvider);
    final activeStoreId = ref.watch(activeStoreIdProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Enterprise Branches', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.campaign_rounded),
            tooltip: 'Dispatch Broadcast',
            onPressed: _openBroadcastDialog,
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
            onPressed: () {
              ref.invalidate(adminBranchesProvider);
              ref.invalidate(adminGlobalAnalyticsProvider);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(adminBranchesProvider);
          ref.invalidate(adminGlobalAnalyticsProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Global aggregated KPI banner
              globalAsync.when(
                data: (g) => Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  color: AppColors.forestGreen.withValues(alpha: 0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.public_rounded, color: AppColors.forestGreen),
                            SizedBox(width: 8),
                            Text(
                              'Global Enterprise Overview',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.forestGreen,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            _buildKpiItem('Total Stores', '${g['total_stores']}'),
                            _buildKpiItem('Total SKUs', '${g['total_products']}'),
                            _buildKpiItem('Active Stock', '${g['total_active_stock']}'),
                            _buildKpiItem('Saved Food', '${g['total_diverted_kg']} kg'),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                loading: () => const LinearProgressIndicator(),
                error: (error, stackTrace) => const SizedBox.shrink(),
              ),
              const SizedBox(height: 16),
              const Text(
                'Retail Store Branches',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              branchesAsync.when(
                data: (branches) {
                  if (branches.isEmpty) {
                    return const Center(child: Text('No branches registered yet.'));
                  }
                  return ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: branches.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final b = branches[index];
                      final storeId = b['id'] as int;
                      final isSelected = storeId == activeStoreId;
                      final mgr = b['manager'] as Map<String, dynamic>?;

                      return Card(
                        elevation: isSelected ? 3 : 1,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: isSelected
                              ? const BorderSide(color: AppColors.forestGreen, width: 2)
                              : BorderSide.none,
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  CircleAvatar(
                                    backgroundColor: isSelected
                                        ? AppColors.forestGreen
                                        : Colors.grey.withValues(alpha: 0.2),
                                    child: Text(
                                      '#$storeId',
                                      style: TextStyle(
                                        color: isSelected ? Colors.white : Colors.black87,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          b['name'] as String? ?? 'Branch #$storeId',
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        Text(
                                          b['location'] as String? ?? '',
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (isSelected)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: AppColors.forestGreen.withValues(alpha: 0.2),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: const Text(
                                        'Active Selection',
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.forestGreen,
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                              const Divider(height: 20),
                              Row(
                                children: [
                                  Icon(Icons.person_outline_rounded, size: 18, color: Colors.grey.shade600),
                                  const SizedBox(width: 6),
                                  Text(
                                    mgr != null
                                        ? 'Manager: ${mgr['full_name']} (${mgr['email']})'
                                        : 'Manager: None assigned',
                                    style: const TextStyle(fontSize: 13),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  Icon(Icons.inventory_2_outlined, size: 18, color: Colors.grey.shade600),
                                  const SizedBox(width: 6),
                                  Text(
                                    '${b['product_count']} Products  •  ${b['active_stock']} Units in Stock',
                                    style: const TextStyle(fontSize: 13),
                                  ),
                                  const Spacer(),
                                  OutlinedButton.icon(
                                    onPressed: () {
                                      ref.read(activeStoreIdProvider.notifier).state = storeId;
                                      context.go('/catalog');
                                    },
                                    icon: const Icon(Icons.arrow_forward_rounded, size: 16),
                                    label: const Text('View Catalog'),
                                    style: OutlinedButton.styleFrom(
                                      visualDensity: VisualDensity.compact,
                                      foregroundColor: AppColors.forestGreen,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  );
                },
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: CircularProgressIndicator(),
                  ),
                ),
                error: (e, stackTrace) => Center(child: Text('Error loading branches: $e')),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openCreateBranchDialog,
        backgroundColor: AppColors.forestGreen,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_business_rounded),
        label: const Text('Create Branch', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildKpiItem(String title, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 2),
        Text(title, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
      ],
    );
  }
}
