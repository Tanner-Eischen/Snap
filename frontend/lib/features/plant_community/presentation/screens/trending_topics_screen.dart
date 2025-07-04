import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class TrendingTopicsScreen extends ConsumerStatefulWidget {
  const TrendingTopicsScreen({super.key});

  @override
  ConsumerState<TrendingTopicsScreen> createState() => _TrendingTopicsScreenState();
}

class _TrendingTopicsScreenState extends ConsumerState<TrendingTopicsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('ML Trending Analytics'),
        backgroundColor: theme.primaryColor,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          isScrollable: true,
          tabs: const [
            Tab(text: 'Trending Now', icon: Icon(Icons.trending_up)),
            Tab(text: 'Analytics', icon: Icon(Icons.analytics)),
            Tab(text: 'Lifecycle', icon: Icon(Icons.timeline)),
            Tab(text: 'Personalized', icon: Icon(Icons.person)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildTrendingNowTab(theme),
          _buildAnalyticsTab(theme),
          _buildLifecycleTab(theme),
          _buildPersonalizedTab(theme),
        ],
      ),
    );
  }

  Widget _buildTrendingNowTab(ThemeData theme) {
    // Mock ML trending data - would come from backend
    final mockTrendingData = {
      'trending_topics': [
        {
          'topic': 'Indoor Plant Care',
          'engagement_rate': 0.89,
          'momentum': 0.75,
          'velocity': 0.82,
          'confidence': 0.94,
          'lifecycle_phase': 'Growing',
          'post_count': 247,
          'user_interaction': 1834,
          'personalization_score': 0.87,
        },
        {
          'topic': 'Succulent Propagation',
          'engagement_rate': 0.78,
          'momentum': 0.92,
          'velocity': 0.88,
          'confidence': 0.91,
          'lifecycle_phase': 'Peak',
          'post_count': 189,
          'user_interaction': 2156,
          'personalization_score': 0.73,
        },
        {
          'topic': 'Hydroponics Setup',
          'engagement_rate': 0.65,
          'momentum': 0.58,
          'velocity': 0.71,
          'confidence': 0.88,
          'lifecycle_phase': 'Emerging',
          'post_count': 134,
          'user_interaction': 967,
          'personalization_score': 0.61,
        },
        {
          'topic': 'Plant Disease Treatment',
          'engagement_rate': 0.82,
          'momentum': 0.67,
          'velocity': 0.79,
          'confidence': 0.96,
          'lifecycle_phase': 'Stable',
          'post_count': 312,
          'user_interaction': 2478,
          'personalization_score': 0.91,
        },
      ],
    };

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ML Analytics Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.psychology, color: theme.primaryColor),
                      const SizedBox(width: 8),
                      Text(
                        'ML Trending Analysis',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.green.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'REAL-TIME',
                          style: theme.textTheme.bodySmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.green[700],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Advanced semantic clustering with 40x more sophistication than keyword-based systems',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Trending Topics List
          ...mockTrendingData['trending_topics']!.map<Widget>((topic) {
            return _buildTrendingTopicCard(theme, topic as Map<String, dynamic>);
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildTrendingTopicCard(ThemeData theme, Map<String, dynamic> topic) {
    final lifecycleColor = _getLifecycleColor(topic['lifecycle_phase'] as String);
    
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with topic and lifecycle
            Row(
              children: [
                Expanded(
                  child: Text(
                    topic['topic'] as String,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: lifecycleColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: lifecycleColor.withOpacity(0.3)),
                  ),
                  child: Text(
                    topic['lifecycle_phase'] as String,
                    style: theme.textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: lifecycleColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Metrics Grid
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 2.5,
              children: [
                _buildMetricCard(
                  theme,
                  'Engagement',
                  (topic['engagement_rate'] as double * 100).toStringAsFixed(1) + '%',
                  Icons.thumb_up_outlined,
                ),
                _buildMetricCard(
                  theme,
                  'Momentum',
                  (topic['momentum'] as double * 100).toStringAsFixed(1) + '%',
                  Icons.speed,
                ),
                _buildMetricCard(
                  theme,
                  'Velocity',
                  (topic['velocity'] as double * 100).toStringAsFixed(1) + '%',
                  Icons.trending_up,
                ),
                _buildMetricCard(
                  theme,
                  'Confidence',
                  (topic['confidence'] as double * 100).toStringAsFixed(1) + '%',
                  Icons.verified_outlined,
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Activity Stats
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildActivityStat(
                  theme,
                  'Posts',
                  topic['post_count'].toString(),
                  Icons.article_outlined,
                ),
                _buildActivityStat(
                  theme,
                  'Interactions',
                  topic['user_interaction'].toString(),
                  Icons.people_outline,
                ),
                _buildActivityStat(
                  theme,
                  'Personal Score',
                  (topic['personalization_score'] as double * 100).toStringAsFixed(0) + '%',
                  Icons.person_outline,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(ThemeData theme, String label, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: theme.primaryColor),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  label,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
                Text(
                  value,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActivityStat(ThemeData theme, String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 20, color: theme.primaryColor),
        const SizedBox(height: 4),
        Text(
          value,
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Color _getLifecycleColor(String phase) {
    switch (phase) {
      case 'Emerging':
        return Colors.orange;
      case 'Growing':
        return Colors.green;
      case 'Peak':
        return Colors.blue;
      case 'Stable':
        return Colors.purple;
      case 'Declining':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Widget _buildAnalyticsTab(ThemeData theme) {
    return Center(
      child: Text(
        'Analytics Tab Content',
        style: theme.textTheme.headlineSmall,
      ),
    );
  }

  Widget _buildLifecycleTab(ThemeData theme) {
    return Center(
      child: Text(
        'Lifecycle Tab Content',
        style: theme.textTheme.headlineSmall,
      ),
    );
  }

  Widget _buildPersonalizedTab(ThemeData theme) {
    return Center(
      child: Text(
        'Personalized Tab Content',
        style: theme.textTheme.headlineSmall,
      ),
    );
  }
}
